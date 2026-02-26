from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from app.config import get_settings
from app.main import create_app


def test_get_type_history_groups_adjacent_events_by_299_300_301_seconds(database_url: str) -> None:
    client = TestClient(create_app())
    engine = create_engine(database_url)

    try:
        created = client.post("/api/v1/types", json={"name": "Necrons"})
        assert created.status_code == 201

        with engine.begin() as connection:
            connection.execute(
                text(
                    """
                    INSERT INTO history_logs (type_id, from_stage, to_stage, qty, created_at)
                    VALUES
                        (1, 'IN_BOX', 'BUILDING', 1, '2026-02-25 10:00:00'),
                        (1, 'IN_BOX', 'BUILDING', 2, '2026-02-25 10:04:59'),
                        (1, 'IN_BOX', 'BUILDING', 3, '2026-02-25 10:09:59'),
                        (1, 'IN_BOX', 'BUILDING', 4, '2026-02-25 10:15:00')
                    """
                )
            )

        response = client.get("/api/v1/types/1/history")
    finally:
        get_settings.cache_clear()

    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 2
    assert body["items"][0] == {
        "from_stage": "IN_BOX",
        "to_stage": "BUILDING",
        "qty": 6,
        "timestamp": "2026-02-25T10:00:00Z",
    }
    assert body["items"][1] == {
        "from_stage": "IN_BOX",
        "to_stage": "BUILDING",
        "qty": 4,
        "timestamp": "2026-02-25T10:15:00Z",
    }


def test_get_type_history_does_not_group_non_adjacent_equal_transitions(database_url: str) -> None:
    client = TestClient(create_app())
    engine = create_engine(database_url)

    try:
        created = client.post("/api/v1/types", json={"name": "Aeldari"})
        assert created.status_code == 201

        with engine.begin() as connection:
            connection.execute(
                text(
                    """
                    INSERT INTO history_logs (type_id, from_stage, to_stage, qty, created_at)
                    VALUES
                        (1, 'IN_BOX', 'BUILDING', 2, '2026-02-25 11:00:00'),
                        (1, 'BUILDING', 'PRIMING', 5, '2026-02-25 11:01:00'),
                        (1, 'IN_BOX', 'BUILDING', 3, '2026-02-25 11:02:00')
                    """
                )
            )

        response = client.get("/api/v1/types/1/history")
    finally:
        get_settings.cache_clear()

    assert response.status_code == 200
    assert response.json() == {
        "items": [
            {
                "from_stage": "IN_BOX",
                "to_stage": "BUILDING",
                "qty": 2,
                "timestamp": "2026-02-25T11:00:00Z",
            },
            {
                "from_stage": "BUILDING",
                "to_stage": "PRIMING",
                "qty": 5,
                "timestamp": "2026-02-25T11:01:00Z",
            },
            {
                "from_stage": "IN_BOX",
                "to_stage": "BUILDING",
                "qty": 3,
                "timestamp": "2026-02-25T11:02:00Z",
            },
        ]
    }
