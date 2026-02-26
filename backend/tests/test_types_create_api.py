from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import text

from app.domain.stages import STAGES


def test_post_types_creates_type_and_returns_zero_counts(client: TestClient, db_engine) -> None:

    if True:
        response = client.post("/api/v1/types", json={"name": "Orks"})
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

    with db_engine.begin() as connection:
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


def test_post_types_returns_duplicate_error_for_existing_name(
    client: TestClient, db_engine
) -> None:

    if True:
        first_response = client.post("/api/v1/types", json={"name": "Aeldari"})
        second_response = client.post("/api/v1/types", json={"name": "Aeldari"})
    assert first_response.status_code == 201
    assert second_response.status_code == 400
    assert second_response.json() == {
        "code": "ERR_DUPLICATE_TYPE_NAME",
        "message": "Miniature type with this name already exists.",
    }
