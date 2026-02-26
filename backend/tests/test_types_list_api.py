from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from app.config import get_settings
from app.main import create_app


def test_get_types_returns_empty_list_for_empty_database(database_url: str) -> None:

    try:
        response = TestClient(create_app()).get("/api/v1/types")
    finally:
        get_settings.cache_clear()

    assert response.status_code == 200
    assert response.json() == {"items": []}


def test_get_types_returns_sorted_types_with_all_stage_counts(database_url: str) -> None:

    engine = create_engine(database_url)
    with engine.begin() as connection:
        connection.execute(
            text("INSERT INTO miniature_types (name) VALUES (:name)"),
            [{"name": "Zeta"}, {"name": "Alpha"}],
        )
        connection.execute(
            text(
                """
                UPDATE stage_counts
                SET count = CASE
                    WHEN stage_name = 'IN_BOX' THEN 4
                    WHEN stage_name = 'BUILDING' THEN 2
                    WHEN stage_name = 'PAINTING' THEN 1
                    ELSE count
                END
                WHERE type_id = (SELECT id FROM miniature_types WHERE name = 'Alpha')
                """
            )
        )

    try:
        response = TestClient(create_app()).get("/api/v1/types")
    finally:
        get_settings.cache_clear()

    assert response.status_code == 200
    assert response.json() == {
        "items": [
            {
                "id": 2,
                "name": "Alpha",
                "counts": {
                    "in_box": 4,
                    "building": 2,
                    "priming": 0,
                    "painting": 1,
                    "done": 0,
                },
            },
            {
                "id": 1,
                "name": "Zeta",
                "counts": {
                    "in_box": 0,
                    "building": 0,
                    "priming": 0,
                    "painting": 0,
                    "done": 0,
                },
            },
        ]
    }
