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


def test_get_types_returns_empty_list_for_empty_database(tmp_path: Path, monkeypatch) -> None:
    db_file = tmp_path / "types_list_empty.db"
    _migrate_sqlite_database(db_file, monkeypatch)

    try:
        response = TestClient(create_app()).get("/api/v1/types")
    finally:
        get_settings.cache_clear()

    assert response.status_code == 200
    assert response.json() == {"items": []}


def test_get_types_returns_sorted_types_with_all_stage_counts(tmp_path: Path, monkeypatch) -> None:
    db_file = tmp_path / "types_list_with_data.db"
    database_url = _migrate_sqlite_database(db_file, monkeypatch)

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
