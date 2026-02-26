from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from app.config import get_settings
from app.domain.stages import STAGES
from app.main import create_app




def test_post_types_creates_type_and_returns_zero_counts(database_url: str) -> None:

    try:
        response = TestClient(create_app()).post("/api/v1/types", json={"name": "Orks"})
    finally:
        get_settings.cache_clear()

    assert response.status_code == 201
    assert response.json() == {
        "id": 1,
        "name": "Orks",
        "counts": {
            "in_box": 0,
            "building": 0,
            "priming": 0,
            "painting": 0,
            "done": 0,
        },
    }

    engine = create_engine(database_url)
    with engine.begin() as connection:
        stage_counts = connection.execute(
            text(
                """
                SELECT sc.stage_name, sc.count
                FROM stage_counts sc
                JOIN miniature_types mt ON mt.id = sc.type_id
                WHERE mt.name = :name
                """
            ),
            {"name": "Orks"},
        ).mappings()
        counts_by_stage = {row["stage_name"]: row["count"] for row in stage_counts}

    assert counts_by_stage == {stage: 0 for stage in STAGES}


def test_post_types_returns_duplicate_error_for_existing_name(database_url: str) -> None:

    try:
        client = TestClient(create_app())
        first_response = client.post("/api/v1/types", json={"name": "Aeldari"})
        second_response = client.post("/api/v1/types", json={"name": "Aeldari"})
    finally:
        get_settings.cache_clear()

    assert first_response.status_code == 201
    assert second_response.status_code == 400
    assert second_response.json() == {
        "code": "ERR_DUPLICATE_TYPE_NAME",
        "message": "Miniature type with this name already exists.",
    }
