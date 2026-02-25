from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime

from fastapi import APIRouter, Body, Depends, HTTPException, status
from pydantic import ValidationError
from sqlalchemy import Select, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.v1.errors import ApiContractError, ErrorCode
from app.api.v1.schemas import (
    ApiStatusResponse,
    ExportHistoryItem,
    ExportResponse,
    ExportStageCount,
    ExportTypeItem,
    ImportRequest,
    ImportResponse,
    ImportTypeItem,
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


def _iter_export_rows(db_session: Session) -> Iterator[tuple[int, str, str, int]]:
    stmt: Select[tuple[int, str, str, int]] = (
        select(
            MiniatureType.id,
            MiniatureType.name,
            StageCount.stage_name,
            StageCount.count,
        )
        .select_from(MiniatureType)
        .join(StageCount, StageCount.type_id == MiniatureType.id)
        .order_by(MiniatureType.name.asc(), MiniatureType.id.asc())
    )
    rows = db_session.execute(stmt).all()
    return ((row[0], row[1], row[2], row[3]) for row in rows)


def _iter_export_history_rows(
    db_session: Session,
) -> Iterator[tuple[int, str, str, int, datetime]]:
    stmt: Select[tuple[int, str, str, int, datetime]] = select(
        HistoryLog.type_id,
        HistoryLog.from_stage,
        HistoryLog.to_stage,
        HistoryLog.qty,
        HistoryLog.created_at,
    ).order_by(HistoryLog.type_id.asc(), HistoryLog.created_at.asc(), HistoryLog.id.asc())
    rows = db_session.execute(stmt).all()
    return ((row[0], row[1], row[2], row[3], row[4]) for row in rows)


def _parse_import_payload(raw_payload: dict[str, object]) -> ImportRequest:
    try:
        return ImportRequest.model_validate(raw_payload)
    except ValidationError as error:
        raise ApiContractError(
            code=ErrorCode.ERR_INVALID_IMPORT_FORMAT,
            message="Import payload is invalid.",
        ) from error


def _build_stage_delta_map(item: ImportTypeItem) -> dict[str, int]:
    stage_delta_by_name: dict[str, int] = {}
    for stage_count in item.stage_counts:
        stage_name = stage_count.stage.value
        if stage_name in stage_delta_by_name:
            raise ApiContractError(
                code=ErrorCode.ERR_INVALID_IMPORT_FORMAT,
                message="Import payload is invalid.",
            )
        stage_delta_by_name[stage_name] = stage_count.count

    expected_stages = {stage.value for stage in StageCode}
    if set(stage_delta_by_name.keys()) != expected_stages:
        raise ApiContractError(
            code=ErrorCode.ERR_INVALID_IMPORT_FORMAT,
            message="Import payload is invalid.",
        )

    return stage_delta_by_name


def _resolve_type_for_import(db_session: Session, type_name: str) -> MiniatureType:
    existing_type = db_session.execute(
        select(MiniatureType).where(MiniatureType.name == type_name)
    ).scalar_one_or_none()
    if existing_type is not None:
        return existing_type

    created_type = MiniatureType(name=type_name)
    db_session.add(created_type)
    db_session.flush()
    return created_type


def _apply_import_stage_deltas(
    db_session: Session, type_id: int, stage_delta_by_name: dict[str, int]
) -> None:
    stage_rows = db_session.execute(
        select(StageCount).where(StageCount.type_id == type_id).with_for_update()
    ).scalars()
    stage_rows_by_name = {row.stage_name: row for row in stage_rows}

    for stage in StageCode:
        stage_row = stage_rows_by_name.get(stage.value)
        if stage_row is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Stage counts are not initialized for this type.",
            )
        stage_row.count += stage_delta_by_name[stage.value]


def _append_import_history(db_session: Session, type_id: int, item: ImportTypeItem) -> None:
    for history_item in item.history:
        db_session.add(
            HistoryLog(
                type_id=type_id,
                from_stage=history_item.from_stage.value,
                to_stage=history_item.to_stage.value,
                qty=history_item.qty,
                created_at=history_item.created_at,
            )
        )


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


@router.get("/export", tags=["import-export"], response_model=ExportResponse)
def export_state(db_session: Session = Depends(get_db_session)) -> ExportResponse:
    type_names: dict[int, str] = {}
    stage_counts_by_type_id: dict[int, dict[str, int]] = {}
    history_by_type_id: dict[int, list[ExportHistoryItem]] = {}

    for type_id, name, stage_name, count in _iter_export_rows(db_session):
        type_names[type_id] = name
        if type_id not in stage_counts_by_type_id:
            stage_counts_by_type_id[type_id] = _base_counts()
        stage_counts_by_type_id[type_id][stage_name] = count

    for type_id, from_stage, to_stage, qty, created_at in _iter_export_history_rows(db_session):
        if type_id not in history_by_type_id:
            history_by_type_id[type_id] = []
        history_by_type_id[type_id].append(
            ExportHistoryItem(
                from_stage=StageCode(from_stage),
                to_stage=StageCode(to_stage),
                qty=qty,
                created_at=created_at,
            )
        )

    export_items: list[ExportTypeItem] = []
    for type_id, name in type_names.items():
        stage_counts = stage_counts_by_type_id.get(type_id, _base_counts())
        export_items.append(
            ExportTypeItem(
                name=name,
                stage_counts=[
                    ExportStageCount(stage=stage, count=stage_counts[stage.value])
                    for stage in StageCode
                ],
                history=history_by_type_id.get(type_id, []),
            )
        )

    return ExportResponse(types=export_items)


@router.post("/import", tags=["import-export"], response_model=ImportResponse)
def import_state(
    raw_payload: dict[str, object] = Body(...),
    db_session: Session = Depends(get_db_session),
) -> ImportResponse:
    payload = _parse_import_payload(raw_payload)

    try:
        with db_session.begin():
            for type_item in payload.types:
                stage_delta_by_name = _build_stage_delta_map(type_item)
                target_type = _resolve_type_for_import(db_session, type_item.name)
                _apply_import_stage_deltas(db_session, target_type.id, stage_delta_by_name)
                _append_import_history(db_session, target_type.id, type_item)
    except ApiContractError:
        raise
    except IntegrityError as error:
        raise ApiContractError(
            code=ErrorCode.ERR_INVALID_IMPORT_FORMAT,
            message="Import payload is invalid.",
        ) from error

    return ImportResponse(status="ok")
