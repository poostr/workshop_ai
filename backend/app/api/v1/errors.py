from __future__ import annotations

from enum import StrEnum

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.v1.schemas import ErrorResponse


class ErrorCode(StrEnum):
    ERR_VALIDATION = "ERR_VALIDATION"
    ERR_INVALID_STAGE = "ERR_INVALID_STAGE"
    ERR_INVALID_STAGE_TRANSITION = "ERR_INVALID_STAGE_TRANSITION"
    ERR_INSUFFICIENT_QTY = "ERR_INSUFFICIENT_QTY"
    ERR_DUPLICATE_TYPE_NAME = "ERR_DUPLICATE_TYPE_NAME"


class ApiContractError(Exception):
    def __init__(self, code: ErrorCode, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


def register_api_exception_handlers(app) -> None:
    @app.exception_handler(ApiContractError)
    async def handle_api_contract_error(_request: Request, exc: ApiContractError) -> JSONResponse:
        payload = ErrorResponse(code=exc.code.value, message=exc.message)
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=payload.model_dump())

    @app.exception_handler(RequestValidationError)
    async def handle_request_validation_error(
        _request: Request, _exc: RequestValidationError
    ) -> JSONResponse:
        payload = ErrorResponse(
            code=ErrorCode.ERR_VALIDATION.value,
            message="Request validation failed.",
        )
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=payload.model_dump())
