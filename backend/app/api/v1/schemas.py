from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

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


class ExportStageCount(BaseModel):
    stage: StageCode
    count: int


class ExportHistoryItem(BaseModel):
    from_stage: StageCode
    to_stage: StageCode
    qty: int
    created_at: datetime


class ExportTypeItem(BaseModel):
    name: str
    stage_counts: list[ExportStageCount]
    history: list[ExportHistoryItem]


class ExportResponse(BaseModel):
    types: list[ExportTypeItem]


class ImportStageCount(BaseModel):
    model_config = ConfigDict(extra="forbid")

    stage: StageCode
    count: int = Field(strict=True, ge=0, le=1_000_000)


class ImportHistoryItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    from_stage: StageCode
    to_stage: StageCode
    qty: int = Field(strict=True, gt=0, le=1_000_000)
    created_at: datetime


class ImportTypeItem(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=255)
    stage_counts: list[ImportStageCount]
    history: list[ImportHistoryItem]

    @model_validator(mode="after")
    def validate_stage_counts_cover_all_stages(self) -> "ImportTypeItem":
        stage_values = [stage_count.stage for stage_count in self.stage_counts]
        if len(stage_values) != len(StageCode):
            raise ValueError("stage_counts must contain every stage exactly once")
        if len(set(stage_values)) != len(StageCode):
            raise ValueError("stage_counts must contain unique stages")
        return self


class ImportRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    types: list[ImportTypeItem]


class ImportResponse(BaseModel):
    status: str
