from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from app.config import get_settings
from app.main import create_app


def test_post_import_merges_counts_and_appends_history(database_url: str) -> None:
    client = TestClient(create_app())
    engine = create_engine(database_url)

    try:
        created = client.post("/api/v1/types", json={"name": "Alpha"})
        assert created.status_code == 201

        with engine.begin() as connection:
            connection.execute(
                text(
                    """
                    UPDATE stage_counts
                    SET count = CASE
                        WHEN stage_name = 'IN_BOX' THEN 10
                        WHEN stage_name = 'BUILDING' THEN 2
                        ELSE count
                    END
                    WHERE type_id = 1
                    """
                )
            )
            connection.execute(
                text(
                    """
                    INSERT INTO history_logs (type_id, from_stage, to_stage, qty, created_at)
                    VALUES (1, 'IN_BOX', 'BUILDING', 1, '2026-02-25 08:00:00')
                    """
                )
            )

        response = client.post(
            "/api/v1/import",
            json={
                "types": [
                    {
                        "name": "Alpha",
                        "stage_counts": [
                            {"stage": "IN_BOX", "count": 3},
                            {"stage": "BUILDING", "count": 1},
                            {"stage": "PRIMING", "count": 4},
                            {"stage": "PAINTING", "count": 0},
                            {"stage": "DONE", "count": 2},
                        ],
                        "history": [
                            {
                                "from_stage": "BUILDING",
                                "to_stage": "PRIMING",
                                "qty": 2,
                                "created_at": "2026-02-25T09:00:00Z",
                            }
                        ],
                    },
                    {
                        "name": "Beta",
                        "stage_counts": [
                            {"stage": "IN_BOX", "count": 5},
                            {"stage": "BUILDING", "count": 0},
                            {"stage": "PRIMING", "count": 0},
                            {"stage": "PAINTING", "count": 1},
                            {"stage": "DONE", "count": 0},
                        ],
                        "history": [
                            {
                                "from_stage": "IN_BOX",
                                "to_stage": "PAINTING",
                                "qty": 1,
                                "created_at": "2026-02-25T10:00:00Z",
                            }
                        ],
                    },
                ]
            },
        )
        export_response = client.get("/api/v1/export")
    finally:
        get_settings.cache_clear()

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert export_response.status_code == 200
    assert export_response.json() == {
        "types": [
            {
                "name": "Alpha",
                "stage_counts": [
                    {"stage": "IN_BOX", "count": 13},
                    {"stage": "BUILDING", "count": 3},
                    {"stage": "PRIMING", "count": 4},
                    {"stage": "PAINTING", "count": 0},
                    {"stage": "DONE", "count": 2},
                ],
                "history": [
                    {
                        "from_stage": "IN_BOX",
                        "to_stage": "BUILDING",
                        "qty": 1,
                        "created_at": "2026-02-25T08:00:00Z",
                    },
                    {
                        "from_stage": "BUILDING",
                        "to_stage": "PRIMING",
                        "qty": 2,
                        "created_at": "2026-02-25T09:00:00Z",
                    },
                ],
            },
            {
                "name": "Beta",
                "stage_counts": [
                    {"stage": "IN_BOX", "count": 5},
                    {"stage": "BUILDING", "count": 0},
                    {"stage": "PRIMING", "count": 0},
                    {"stage": "PAINTING", "count": 1},
                    {"stage": "DONE", "count": 0},
                ],
                "history": [
                    {
                        "from_stage": "IN_BOX",
                        "to_stage": "PAINTING",
                        "qty": 1,
                        "created_at": "2026-02-25T10:00:00Z",
                    }
                ],
            },
        ]
    }


def test_post_import_rolls_back_all_changes_on_invalid_payload(database_url: str) -> None:
    client = TestClient(create_app())
    engine = create_engine(database_url)

    try:
        created = client.post("/api/v1/types", json={"name": "Base"})
        assert created.status_code == 201

        with engine.begin() as connection:
            connection.execute(
                text(
                    """
                    UPDATE stage_counts
                    SET count = 10
                    WHERE type_id = 1 AND stage_name = 'IN_BOX'
                    """
                )
            )

        response = client.post(
            "/api/v1/import",
            json={
                "types": [
                    {
                        "name": "Base",
                        "stage_counts": [
                            {"stage": "IN_BOX", "count": 2},
                            {"stage": "BUILDING", "count": 0},
                            {"stage": "PRIMING", "count": 0},
                            {"stage": "PAINTING", "count": 0},
                            {"stage": "DONE", "count": 0},
                        ],
                        "history": [],
                    },
                    {
                        "name": "Broken",
                        "stage_counts": [
                            {"stage": "IN_BOX", "count": 1},
                            {"stage": "IN_BOX", "count": 2},
                            {"stage": "PRIMING", "count": 0},
                            {"stage": "PAINTING", "count": 0},
                            {"stage": "DONE", "count": 0},
                        ],
                        "history": [],
                    },
                ]
            },
        )
    finally:
        get_settings.cache_clear()

    assert response.status_code == 400
    assert response.json() == {
        "code": "ERR_INVALID_IMPORT_FORMAT",
        "message": "Import payload is invalid.",
    }

    with engine.begin() as connection:
        in_box_count = connection.execute(
            text(
                """
                SELECT count
                FROM stage_counts
                WHERE type_id = 1 AND stage_name = 'IN_BOX'
                """
            )
        ).scalar_one()
        broken_type_count = connection.execute(
            text("SELECT COUNT(*) FROM miniature_types WHERE name = 'Broken'")
        ).scalar_one()
        history_count = connection.execute(text("SELECT COUNT(*) FROM history_logs")).scalar_one()

    assert in_box_count == 10
    assert broken_type_count == 0
    assert history_count == 0


def test_post_import_rejects_missing_stage_counts(database_url: str) -> None:
    client = TestClient(create_app())

    try:
        response = client.post(
            "/api/v1/import",
            json={
                "types": [
                    {
                        "name": "Gamma",
                        "stage_counts": [
                            {"stage": "IN_BOX", "count": 1},
                            {"stage": "BUILDING", "count": 0},
                            {"stage": "PRIMING", "count": 0},
                            {"stage": "PAINTING", "count": 0},
                        ],
                        "history": [],
                    }
                ]
            },
        )
    finally:
        get_settings.cache_clear()

    assert response.status_code == 400
    assert response.json() == {
        "code": "ERR_INVALID_IMPORT_FORMAT",
        "message": "Import payload is invalid.",
    }
