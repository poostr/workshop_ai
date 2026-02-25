from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domain.stages import StageCode


class ApiStatusResponse(BaseModel):
    status: str
    version: str


class ErrorResponse(BaseModel):
    code: str
    message: str


class TypeMoveRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    from_stage: StageCode
    to_stage: StageCode
    qty: int = Field(strict=True, gt=0, le=1_000_000)


class TypeCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=255)


class TypeStageCounts(BaseModel):
    in_box: int
    building: int
    priming: int
    painting: int
    done: int


class TypeListItem(BaseModel):
    id: int
    name: str
    counts: TypeStageCounts


class TypeListResponse(BaseModel):
    items: list[TypeListItem]


class TypeHistoryGroup(BaseModel):
    from_stage: StageCode
    to_stage: StageCode
    qty: int
    timestamp: datetime


class TypeHistoryResponse(BaseModel):
    items: list[TypeHistoryGroup]
