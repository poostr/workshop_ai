from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

from app.config import get_settings
from app.domain.stages import STAGES


def test_alembic_upgrade_head_creates_schema(tmp_path: Path, monkeypatch) -> None:
    db_file = tmp_path / "alembic_test.db"
    database_url = f"sqlite+pysqlite:///{db_file}"

    monkeypatch.setenv("DATABASE_URL", database_url)
    get_settings.cache_clear()

    try:
        alembic_config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
        command.upgrade(alembic_config, "head")
    finally:
        get_settings.cache_clear()

    engine = create_engine(database_url)
    inspector = inspect(engine)

    assert set(inspector.get_table_names()) == {
        "alembic_version",
        "history_logs",
        "miniature_types",
        "stage_counts",
    }


def test_type_insert_seeds_all_stage_counts(tmp_path: Path, monkeypatch) -> None:
    db_file = tmp_path / "alembic_test.db"
    database_url = f"sqlite+pysqlite:///{db_file}"

    monkeypatch.setenv("DATABASE_URL", database_url)
    get_settings.cache_clear()

    try:
        alembic_config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
        command.upgrade(alembic_config, "head")
    finally:
        get_settings.cache_clear()

    engine = create_engine(database_url)
    with engine.begin() as connection:
        connection.execute(
            text("INSERT INTO miniature_types (name) VALUES (:name)"),
            {"name": "Space Marines"},
        )
        rows = connection.execute(
            text(
                """
                SELECT sc.stage_name, sc.count
                FROM stage_counts sc
                JOIN miniature_types mt ON mt.id = sc.type_id
                WHERE mt.name = :name
                """
            ),
            {"name": "Space Marines"},
        ).mappings()

        stage_counts = {row["stage_name"]: row["count"] for row in rows}

    assert stage_counts == {stage: 0 for stage in STAGES}
