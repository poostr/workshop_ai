from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import text



def test_get_export_returns_empty_types_list_for_empty_database(
    client: TestClient, db_engine
) -> None:

    if True:
        response = client.get("/api/v1/export")
    assert response.status_code == 200
    assert response.json() == {"types": []}


def test_get_export_returns_types_counts_and_full_history(client: TestClient, db_engine) -> None:

    if True:
        first = client.post("/api/v1/types", json={"name": "Zeta"})
        second = client.post("/api/v1/types", json={"name": "Alpha"})
        assert first.status_code == 201
        assert second.status_code == 201

        with db_engine.begin() as connection:
            connection.execute(
                text(
                    """
                    UPDATE stage_counts
                    SET count = CASE
                        WHEN stage_name = 'IN_BOX' THEN 7
                        WHEN stage_name = 'BUILDING' THEN 3
                        ELSE count
                    END
                    WHERE type_id = :type_id
                    """
                ),
                {"type_id": 2},
            )
            connection.execute(
                text(
                    """
                    INSERT INTO history_logs (type_id, from_stage, to_stage, qty, created_at)
                    VALUES
                        (2, 'IN_BOX', 'BUILDING', 2, '2026-02-25 09:00:00'),
                        (2, 'BUILDING', 'PAINTING', 1, '2026-02-25 09:10:00'),
                        (1, 'IN_BOX', 'PRIMING', 4, '2026-02-25 10:00:00')
                    """
                )
            )

        response = client.get("/api/v1/export")
    assert response.status_code == 200
    assert response.json() == {
        "types": [
            {
                "name": "Alpha",
                "stage_counts": [
                    {"stage": "IN_BOX", "count": 7},
                    {"stage": "BUILDING", "count": 3},
                    {"stage": "PRIMING", "count": 0},
                    {"stage": "PAINTING", "count": 0},
                    {"stage": "DONE", "count": 0},
                ],
                "history": [
                    {
                        "from_stage": "IN_BOX",
                        "to_stage": "BUILDING",
                        "qty": 2,
                        "created_at": "2026-02-25T09:00:00Z",
                    },
                    {
                        "from_stage": "BUILDING",
                        "to_stage": "PAINTING",
                        "qty": 1,
                        "created_at": "2026-02-25T09:10:00Z",
                    },
                ],
            },
            {
                "name": "Zeta",
                "stage_counts": [
                    {"stage": "IN_BOX", "count": 0},
                    {"stage": "BUILDING", "count": 0},
                    {"stage": "PRIMING", "count": 0},
                    {"stage": "PAINTING", "count": 0},
                    {"stage": "DONE", "count": 0},
                ],
                "history": [
                    {
                        "from_stage": "IN_BOX",
                        "to_stage": "PRIMING",
                        "qty": 4,
                        "created_at": "2026-02-25T10:00:00Z",
                    }
                ],
            },
        ]
    }
