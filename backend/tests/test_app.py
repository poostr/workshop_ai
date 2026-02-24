from fastapi.testclient import TestClient

from app.main import create_app


def test_health_endpoint() -> None:
    client = TestClient(create_app())
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_api_v1_router_is_mounted() -> None:
    client = TestClient(create_app())
    response = client.get("/api/v1/status")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "v1"}
