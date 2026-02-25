from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.errors import ApiContractError, ErrorCode
from app.api.v1.schemas import TypeMoveRequest
from app.main import create_app


def test_business_error_has_unified_contract() -> None:
    app = create_app()

    @app.get("/_test/business-error")
    def test_business_error() -> dict[str, str]:
        raise ApiContractError(
            code=ErrorCode.ERR_INVALID_STAGE_TRANSITION,
            message="Invalid transition.",
        )

    response = TestClient(app).get("/_test/business-error")

    assert response.status_code == 400
    assert response.json() == {
        "code": ErrorCode.ERR_INVALID_STAGE_TRANSITION.value,
        "message": "Invalid transition.",
    }


def test_request_validation_uses_contract_format() -> None:
    app = create_app()

    @app.post("/_test/move")
    def test_move(payload: TypeMoveRequest) -> dict[str, int]:
        return {"qty": payload.qty}

    response = TestClient(app).post(
        "/_test/move",
        json={"from_stage": "UNKNOWN_STAGE", "to_stage": "IN_BOX", "qty": 1},
    )

    assert response.status_code == 400
    assert response.json() == {
        "code": ErrorCode.ERR_VALIDATION.value,
        "message": "Request validation failed.",
    }


def test_type_move_request_uses_strict_validation() -> None:
    app = FastAPI()

    @app.post("/_test/move-strict")
    def test_move_strict(payload: TypeMoveRequest) -> dict[str, int]:
        return {"qty": payload.qty}

    response = TestClient(app).post(
        "/_test/move-strict",
        json={"from_stage": "IN_BOX", "to_stage": "PAINTING", "qty": "3"},
    )

    assert response.status_code == 422
