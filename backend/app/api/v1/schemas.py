from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.domain.stages import StageCode


class ApiStatusResponse(BaseModel):
    status: str
    version: str


class ErrorResponse(BaseModel):
    code: str
    message: str


class TypeMoveRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    from_stage: StageCode
    to_stage: StageCode
    qty: int = Field(gt=0, le=1_000_000)
