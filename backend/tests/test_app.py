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


def test_cors_allows_local_nginx_origin() -> None:
    client = TestClient(create_app())
    response = client.options(
        "/api/v1/status",
        headers={
            "Origin": "http://localhost:8080",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:8080"


def test_cors_rejects_unknown_origin() -> None:
    client = TestClient(create_app())
    response = client.options(
        "/api/v1/status",
        headers={
            "Origin": "https://example.com",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers
