from fastapi import APIRouter

from app.api.v1.schemas import ApiStatusResponse

router = APIRouter()


@router.get("/status", tags=["system"], response_model=ApiStatusResponse)
def api_status() -> ApiStatusResponse:
    return ApiStatusResponse(status="ok", version="v1")
