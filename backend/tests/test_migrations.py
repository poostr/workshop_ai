from __future__ import annotations

from sqlalchemy import create_engine, inspect, text

from app.domain.stages import STAGES


def test_alembic_upgrade_head_creates_schema(database_url: str) -> None:
    engine = create_engine(database_url)
    inspector = inspect(engine)

    assert set(inspector.get_table_names()) == {
        "alembic_version",
        "history_logs",
        "miniature_types",
        "stage_counts",
    }


def test_type_insert_seeds_all_stage_counts(database_url: str) -> None:
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
