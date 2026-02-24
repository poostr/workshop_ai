from fastapi import APIRouter

router = APIRouter()


@router.get("/status", tags=["system"])
def api_status() -> dict[str, str]:
    return {"status": "ok", "version": "v1"}

