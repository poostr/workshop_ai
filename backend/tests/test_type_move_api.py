from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import text



def test_post_move_updates_counts_and_writes_history(client: TestClient, db_engine) -> None:

    if True:
        created = client.post("/api/v1/types", json={"name": "Tau"})
        assert created.status_code == 201

        with db_engine.begin() as connection:
            connection.execute(
                text(
                    """
                    UPDATE stage_counts
                    SET count = 9
                    WHERE type_id = :type_id AND stage_name = 'IN_BOX'
                    """
                ),
                {"type_id": 1},
            )

        response = client.post(
            "/api/v1/types/1/move",
            json={"from_stage": "IN_BOX", "to_stage": "PRIMING", "qty": 4},
        )
    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "name": "Tau",
        "counts": {
            "in_box": 5,
            "building": 0,
            "priming": 4,
            "painting": 0,
            "done": 0,
        },
    }

    with db_engine.begin() as connection:
        history_rows = connection.execute(
            text(
                """
                SELECT from_stage, to_stage, qty
                FROM history_logs
                WHERE type_id = :type_id
                ORDER BY id ASC
                """
            ),
            {"type_id": 1},
        ).mappings()
        history = list(history_rows)

    assert history == [{"from_stage": "IN_BOX", "to_stage": "PRIMING", "qty": 4}]


def test_post_move_returns_insufficient_qty_error(client: TestClient, db_engine) -> None:

    if True:
        created = client.post("/api/v1/types", json={"name": "Astra Militarum"})
        assert created.status_code == 201

        response = client.post(
            "/api/v1/types/1/move",
            json={"from_stage": "IN_BOX", "to_stage": "BUILDING", "qty": 1},
        )
    assert response.status_code == 400
    assert response.json() == {
        "code": "ERR_INSUFFICIENT_QTY",
        "message": "Requested quantity exceeds available items in source stage.",
    }

    with db_engine.begin() as connection:
        in_box_count = connection.execute(
            text(
                """
                SELECT count
                FROM stage_counts
                WHERE type_id = :type_id AND stage_name = 'IN_BOX'
                """
            ),
            {"type_id": 1},
        ).scalar_one()
        history_count = connection.execute(
            text("SELECT COUNT(*) FROM history_logs WHERE type_id = :type_id"),
            {"type_id": 1},
        ).scalar_one()

    assert in_box_count == 0
    assert history_count == 0


def test_post_move_returns_invalid_transition_error(client: TestClient, db_engine) -> None:

    if True:
        created = client.post("/api/v1/types", json={"name": "Orks"})
        assert created.status_code == 201

        response = client.post(
            "/api/v1/types/1/move",
            json={"from_stage": "PAINTING", "to_stage": "BUILDING", "qty": 1},
        )
    assert response.status_code == 400
    assert response.json() == {
        "code": "ERR_INVALID_STAGE_TRANSITION",
        "message": "Transition must move forward in the pipeline.",
    }
