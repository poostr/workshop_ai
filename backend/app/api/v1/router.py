from __future__ import annotations

from collections.abc import Iterator

from fastapi import APIRouter, Depends
from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.api.v1.schemas import (
    ApiStatusResponse,
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


@router.get("/types", tags=["types"], response_model=TypeListResponse)
def list_types(db_session: Session = Depends(get_db_session)) -> TypeListResponse:
    items_by_type_id: dict[int, TypeListItem] = {}

    for type_id, name, stage_name, count in _iter_type_stage_rows(db_session):
        if type_id not in items_by_type_id:
            zero_counts = _base_counts()
            items_by_type_id[type_id] = TypeListItem(
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

        if stage_name is None or count is None:
            continue

        if stage_name == StageCode.IN_BOX.value:
            items_by_type_id[type_id].counts.in_box = count
        elif stage_name == StageCode.BUILDING.value:
            items_by_type_id[type_id].counts.building = count
        elif stage_name == StageCode.PRIMING.value:
            items_by_type_id[type_id].counts.priming = count
        elif stage_name == StageCode.PAINTING.value:
            items_by_type_id[type_id].counts.painting = count
        elif stage_name == StageCode.DONE.value:
            items_by_type_id[type_id].counts.done = count

    return TypeListResponse(items=list(items_by_type_id.values()))
