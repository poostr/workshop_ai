from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from app.config import get_settings
from app.main import create_app


def test_get_type_returns_type_details_with_all_stage_counts(database_url: str) -> None:

    engine = create_engine(database_url)
    with engine.begin() as connection:
        connection.execute(
            text("INSERT INTO miniature_types (name) VALUES (:name)"),
            {"name": "Necrons"},
        )
        connection.execute(
            text(
                """
                UPDATE stage_counts
                SET count = CASE
                    WHEN stage_name = 'IN_BOX' THEN 10
                    WHEN stage_name = 'BUILDING' THEN 5
                    WHEN stage_name = 'PRIMING' THEN 3
                    WHEN stage_name = 'PAINTING' THEN 1
                    ELSE count
                END
                WHERE type_id = (SELECT id FROM miniature_types WHERE name = 'Necrons')
                """
            )
        )

    try:
        response = TestClient(create_app()).get("/api/v1/types/1")
    finally:
        get_settings.cache_clear()

    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "name": "Necrons",
        "counts": {
            "in_box": 10,
            "building": 5,
            "priming": 3,
            "painting": 1,
            "done": 0,
        },
    }


def test_get_type_returns_404_for_missing_type(database_url: str) -> None:

    try:
        response = TestClient(create_app()).get("/api/v1/types/999")
    finally:
        get_settings.cache_clear()

    assert response.status_code == 404
    assert response.json() == {"detail": "Type not found."}
