from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import Select, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.v1.errors import ApiContractError, ErrorCode
from app.api.v1.schemas import (
    ApiStatusResponse,
    TypeCreateRequest,
    TypeHistoryGroup,
    TypeHistoryResponse,
    TypeListItem,
    TypeListResponse,
    TypeMoveRequest,
    TypeStageCounts,
)
from app.db.models import HistoryLog, MiniatureType, StageCount
from app.db.session import get_db_session
from app.domain.stages import StageCode, is_forward_transition

router = APIRouter()


@router.get("/status", tags=["system"], response_model=ApiStatusResponse)
def api_status() -> ApiStatusResponse:
    return ApiStatusResponse(status="ok", version="v1")


def _base_counts() -> dict[str, int]:
    return {stage.value: 0 for stage in StageCode}


def _build_type_item(type_id: int, name: str) -> TypeListItem:
    zero_counts = _base_counts()
    return TypeListItem(
        id=type_id,
        name=name,
        counts=TypeStageCounts(
            in_box=zero_counts[StageCode.IN_BOX.value],
            building=zero_counts[StageCode.BUILDING.value],
            priming=zero_counts[StageCode.PRIMING.value],
            painting=zero_counts[StageCode.PAINTING.value],
            done=zero_counts[StageCode.DONE.value],
        ),
    )


def _apply_stage_count(item: TypeListItem, stage_name: str, count: int) -> None:
    if stage_name == StageCode.IN_BOX.value:
        item.counts.in_box = count
    elif stage_name == StageCode.BUILDING.value:
        item.counts.building = count
    elif stage_name == StageCode.PRIMING.value:
        item.counts.priming = count
    elif stage_name == StageCode.PAINTING.value:
        item.counts.painting = count
    elif stage_name == StageCode.DONE.value:
        item.counts.done = count


def _iter_type_stage_rows(db_session: Session) -> Iterator[tuple[int, str, str | None, int | None]]:
    stmt: Select[tuple[int, str, str | None, int | None]] = (
        select(
            MiniatureType.id,
            MiniatureType.name,
            StageCount.stage_name,
            StageCount.count,
        )
        .select_from(MiniatureType)
        .outerjoin(StageCount, StageCount.type_id == MiniatureType.id)
        .order_by(MiniatureType.name.asc(), MiniatureType.id.asc())
    )
    rows = db_session.execute(stmt).all()
    return ((row[0], row[1], row[2], row[3]) for row in rows)


def _iter_type_rows_by_id(
    db_session: Session, type_id: int
) -> Iterator[tuple[int, str, str | None, int | None]]:
    stmt: Select[tuple[int, str, str | None, int | None]] = (
        select(
            MiniatureType.id,
            MiniatureType.name,
            StageCount.stage_name,
            StageCount.count,
        )
        .select_from(MiniatureType)
        .outerjoin(StageCount, StageCount.type_id == MiniatureType.id)
        .where(MiniatureType.id == type_id)
    )
    rows = db_session.execute(stmt).all()
    return ((row[0], row[1], row[2], row[3]) for row in rows)


def _build_type_item_by_id(db_session: Session, type_id: int) -> TypeListItem | None:
    rows = list(_iter_type_rows_by_id(db_session, type_id))
    if not rows:
        return None

    first_row = rows[0]
    item = _build_type_item(type_id=first_row[0], name=first_row[1])
    for _, _, stage_name, count in rows:
        if stage_name is None or count is None:
            continue
        _apply_stage_count(item, stage_name, count)

    return item


def _is_duplicate_type_name_error(error: IntegrityError) -> bool:
    lowered_error = str(error.orig).lower()
    return "uq_miniature_types_name" in lowered_error or "miniature_types.name" in lowered_error


@dataclass
class _HistoryRow:
    from_stage: str
    to_stage: str
    qty: int
    created_at: datetime


def _iter_history_rows(db_session: Session, type_id: int) -> Iterator[_HistoryRow]:
    stmt: Select[HistoryLog] = (
        select(HistoryLog)
        .where(HistoryLog.type_id == type_id)
        .order_by(HistoryLog.created_at.asc(), HistoryLog.id.asc())
    )
    rows = db_session.execute(stmt).scalars().all()
    return (
        _HistoryRow(
            from_stage=row.from_stage,
            to_stage=row.to_stage,
            qty=row.qty,
            created_at=row.created_at,
        )
        for row in rows
    )


def _group_history_rows(rows: Iterator[_HistoryRow]) -> list[TypeHistoryGroup]:
    groups: list[TypeHistoryGroup] = []
    previous_row: _HistoryRow | None = None

    for row in rows:
        if not groups:
            groups.append(
                TypeHistoryGroup(
                    from_stage=StageCode(row.from_stage),
                    to_stage=StageCode(row.to_stage),
                    qty=row.qty,
                    timestamp=row.created_at,
                )
            )
            previous_row = row
            continue

        assert previous_row is not None
        seconds_since_previous_event = (row.created_at - previous_row.created_at).total_seconds()
        is_same_transition = (
            previous_row.from_stage == row.from_stage and previous_row.to_stage == row.to_stage
        )

        if is_same_transition and 0 <= seconds_since_previous_event <= 300:
            groups[-1].qty += row.qty
            previous_row = row
            continue

        groups.append(
            TypeHistoryGroup(
                from_stage=StageCode(row.from_stage),
                to_stage=StageCode(row.to_stage),
                qty=row.qty,
                timestamp=row.created_at,
            )
        )
        previous_row = row

    return groups


@router.post(
    "/types",
    tags=["types"],
    response_model=TypeListItem,
    status_code=status.HTTP_201_CREATED,
)
def create_type(
    payload: TypeCreateRequest,
    db_session: Session = Depends(get_db_session),
) -> TypeListItem:
    created_type = MiniatureType(name=payload.name)
    db_session.add(created_type)

    try:
        db_session.commit()
    except IntegrityError as error:
        db_session.rollback()
        if _is_duplicate_type_name_error(error):
            raise ApiContractError(
                code=ErrorCode.ERR_DUPLICATE_TYPE_NAME,
                message="Miniature type with this name already exists.",
            ) from error
        raise

    db_session.refresh(created_type)
    return _build_type_item(type_id=created_type.id, name=created_type.name)


@router.get("/types/{type_id}", tags=["types"], response_model=TypeListItem)
def get_type(type_id: int, db_session: Session = Depends(get_db_session)) -> TypeListItem:
    item = _build_type_item_by_id(db_session, type_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Type not found.")

    return item


@router.get("/types", tags=["types"], response_model=TypeListResponse)
def list_types(db_session: Session = Depends(get_db_session)) -> TypeListResponse:
    items_by_type_id: dict[int, TypeListItem] = {}

    for type_id, name, stage_name, count in _iter_type_stage_rows(db_session):
        if type_id not in items_by_type_id:
            items_by_type_id[type_id] = _build_type_item(type_id=type_id, name=name)

        if stage_name is None or count is None:
            continue

        _apply_stage_count(items_by_type_id[type_id], stage_name, count)

    return TypeListResponse(items=list(items_by_type_id.values()))


@router.post("/types/{type_id}/move", tags=["types"], response_model=TypeListItem)
def move_type(
    type_id: int,
    payload: TypeMoveRequest,
    db_session: Session = Depends(get_db_session),
) -> TypeListItem:
    if not is_forward_transition(payload.from_stage, payload.to_stage):
        raise ApiContractError(
            code=ErrorCode.ERR_INVALID_STAGE_TRANSITION,
            message="Transition must move forward in the pipeline.",
        )

    selected_type = db_session.get(MiniatureType, type_id)
    if selected_type is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Type not found.")

    stage_rows = db_session.execute(
        select(StageCount)
        .where(
            StageCount.type_id == type_id,
            StageCount.stage_name.in_([payload.from_stage.value, payload.to_stage.value]),
        )
        .with_for_update()
    ).scalars()
    stage_rows_by_name = {row.stage_name: row for row in stage_rows}
    source_stage = stage_rows_by_name.get(payload.from_stage.value)
    destination_stage = stage_rows_by_name.get(payload.to_stage.value)

    if source_stage is None or destination_stage is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Stage counts are not initialized for this type.",
        )

    if source_stage.count < payload.qty:
        raise ApiContractError(
            code=ErrorCode.ERR_INSUFFICIENT_QTY,
            message="Requested quantity exceeds available items in source stage.",
        )

    source_stage.count -= payload.qty
    destination_stage.count += payload.qty
    db_session.add(
        HistoryLog(
            type_id=type_id,
            from_stage=payload.from_stage.value,
            to_stage=payload.to_stage.value,
            qty=payload.qty,
        )
    )
    db_session.commit()

    item = _build_type_item_by_id(db_session, type_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Type not found.")
    return item


@router.get("/types/{type_id}/history", tags=["types"], response_model=TypeHistoryResponse)
def get_type_history(
    type_id: int, db_session: Session = Depends(get_db_session)
) -> TypeHistoryResponse:
    selected_type = db_session.get(MiniatureType, type_id)
    if selected_type is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Type not found.")

    return TypeHistoryResponse(items=_group_history_rows(_iter_history_rows(db_session, type_id)))
