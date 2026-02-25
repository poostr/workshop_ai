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


def test_post_import_merges_counts_and_appends_history(tmp_path: Path, monkeypatch) -> None:
    db_file = tmp_path / "import_merge.db"
    database_url = _migrate_sqlite_database(db_file, monkeypatch)
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
                                "created_at": "2026-02-25T09:00:00",
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
                                "created_at": "2026-02-25T10:00:00",
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
                        "created_at": "2026-02-25T08:00:00",
                    },
                    {
                        "from_stage": "BUILDING",
                        "to_stage": "PRIMING",
                        "qty": 2,
                        "created_at": "2026-02-25T09:00:00",
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
                        "created_at": "2026-02-25T10:00:00",
                    }
                ],
            },
        ]
    }


def test_post_import_rolls_back_all_changes_on_invalid_payload(tmp_path: Path, monkeypatch) -> None:
    db_file = tmp_path / "import_rollback.db"
    database_url = _migrate_sqlite_database(db_file, monkeypatch)
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
