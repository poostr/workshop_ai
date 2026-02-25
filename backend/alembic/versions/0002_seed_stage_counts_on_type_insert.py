"""Seed stage_counts rows on miniature type insert.

Revision ID: 0002_seed_stage_counts_on_type_insert
Revises: 0001_init_schema_placeholder
Create Date: 2026-02-25 12:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002_seed_stage_counts_on_type_insert"
down_revision: str | None = "0001_init_schema_placeholder"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

_TRIGGER_NAME = "trg_seed_stage_counts_after_type_insert"
_FUNCTION_NAME = "seed_stage_counts_for_new_type"


def _create_sqlite_trigger() -> None:
    op.execute(
        f"""
        CREATE TRIGGER {_TRIGGER_NAME}
        AFTER INSERT ON miniature_types
        FOR EACH ROW
        BEGIN
            INSERT INTO stage_counts (type_id, stage_name, count)
            VALUES
                (NEW.id, 'IN_BOX', 0),
                (NEW.id, 'BUILDING', 0),
                (NEW.id, 'PRIMING', 0),
                (NEW.id, 'PAINTING', 0),
                (NEW.id, 'DONE', 0);
        END;
        """
    )


def _create_postgresql_trigger() -> None:
    op.execute(
        f"""
        CREATE OR REPLACE FUNCTION {_FUNCTION_NAME}()
        RETURNS TRIGGER
        AS $$
        BEGIN
            INSERT INTO stage_counts (type_id, stage_name, count)
            VALUES
                (NEW.id, 'IN_BOX', 0),
                (NEW.id, 'BUILDING', 0),
                (NEW.id, 'PRIMING', 0),
                (NEW.id, 'PAINTING', 0),
                (NEW.id, 'DONE', 0);

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        f"""
        CREATE TRIGGER {_TRIGGER_NAME}
        AFTER INSERT ON miniature_types
        FOR EACH ROW
        EXECUTE FUNCTION {_FUNCTION_NAME}();
        """
    )


def upgrade() -> None:
    dialect_name = op.get_bind().dialect.name
    if dialect_name == "sqlite":
        _create_sqlite_trigger()
        return

    _create_postgresql_trigger()


def downgrade() -> None:
    dialect_name = op.get_bind().dialect.name
    op.execute(f"DROP TRIGGER IF EXISTS {_TRIGGER_NAME} ON miniature_types")

    if dialect_name == "postgresql":
        op.execute(f"DROP FUNCTION IF EXISTS {_FUNCTION_NAME}()")
