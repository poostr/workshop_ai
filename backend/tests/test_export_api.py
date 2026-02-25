from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from app.config import get_settings
from app.main import create_app


def _migrate_sqlite_database(db_file: Path, monkeypatch) -> str:
    database_url = f"sqlite+pysqlite:///{db_file}"
    monkeypatch.setenv("DATABASE_URL", database_url)
    get_settings.cache_clear()

    alembic_config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    command.upgrade(alembic_config, "head")

    return database_url


def test_get_export_returns_empty_types_list_for_empty_database(
    tmp_path: Path, monkeypatch
) -> None:
    db_file = tmp_path / "export_empty.db"
    _migrate_sqlite_database(db_file, monkeypatch)
    client = TestClient(create_app())

    try:
        response = client.get("/api/v1/export")
    finally:
        get_settings.cache_clear()

    assert response.status_code == 200
    assert response.json() == {"types": []}


def test_get_export_returns_types_counts_and_full_history(tmp_path: Path, monkeypatch) -> None:
    db_file = tmp_path / "export_with_data.db"
    database_url = _migrate_sqlite_database(db_file, monkeypatch)
    client = TestClient(create_app())
    engine = create_engine(database_url)

    try:
        first = client.post("/api/v1/types", json={"name": "Zeta"})
        second = client.post("/api/v1/types", json={"name": "Alpha"})
        assert first.status_code == 201
        assert second.status_code == 201

        with engine.begin() as connection:
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
    finally:
        get_settings.cache_clear()

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
                        "created_at": "2026-02-25T09:00:00",
                    },
                    {
                        "from_stage": "BUILDING",
                        "to_stage": "PAINTING",
                        "qty": 1,
                        "created_at": "2026-02-25T09:10:00",
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
                        "created_at": "2026-02-25T10:00:00",
                    }
                ],
            },
        ]
    }
