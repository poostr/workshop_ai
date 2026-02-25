from __future__ import annotations

from collections.abc import Iterator

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import Select, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.v1.errors import ApiContractError, ErrorCode
from app.api.v1.schemas import (
    ApiStatusResponse,
    TypeCreateRequest,
    TypeListItem,
    TypeListResponse,
    TypeStageCounts,
)
from app.db.models import MiniatureType, StageCount
from app.db.session import get_db_session
from app.domain.stages import StageCode

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


def _is_duplicate_type_name_error(error: IntegrityError) -> bool:
    lowered_error = str(error.orig).lower()
    return "uq_miniature_types_name" in lowered_error or "miniature_types.name" in lowered_error


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
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Type not found.")

    first_row = rows[0]
    item = _build_type_item(type_id=first_row[0], name=first_row[1])
    for _, _, stage_name, count in rows:
        if stage_name is None or count is None:
            continue
        _apply_stage_count(item, stage_name, count)
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
