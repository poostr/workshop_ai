"""Initial Alembic revision placeholder.

Revision ID: 0001_init_schema_placeholder
Revises:
Create Date: 2026-02-24 00:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.domain.stages import STAGES_SQL_LIST

# revision identifiers, used by Alembic.
revision: str = "0001_init_schema_placeholder"
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

def upgrade() -> None:
    op.create_table(
        "miniature_types",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.UniqueConstraint("name", name="uq_miniature_types_name"),
    )

    op.create_table(
        "stage_counts",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("type_id", sa.Integer(), nullable=False),
        sa.Column("stage_name", sa.String(length=32), nullable=False),
        sa.Column("count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.CheckConstraint("count >= 0", name="ck_stage_counts_count_non_negative"),
        sa.CheckConstraint(
            f"stage_name IN ({STAGES_SQL_LIST})",
            name="ck_stage_counts_stage_name_valid",
        ),
        sa.ForeignKeyConstraint(
            ("type_id",),
            ("miniature_types.id",),
            ondelete="CASCADE",
            name="fk_stage_counts_type_id_miniature_types",
        ),
        sa.UniqueConstraint("type_id", "stage_name", name="uq_stage_counts_type_stage"),
    )
    op.create_table(
        "history_logs",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("type_id", sa.Integer(), nullable=False),
        sa.Column("from_stage", sa.String(length=32), nullable=False),
        sa.Column("to_stage", sa.String(length=32), nullable=False),
        sa.Column("qty", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.CheckConstraint(
            f"from_stage IN ({STAGES_SQL_LIST})",
            name="ck_history_logs_from_stage_valid",
        ),
        sa.CheckConstraint(
            f"to_stage IN ({STAGES_SQL_LIST})",
            name="ck_history_logs_to_stage_valid",
        ),
        sa.CheckConstraint("qty > 0", name="ck_history_logs_qty_positive"),
        sa.ForeignKeyConstraint(
            ("type_id",),
            ("miniature_types.id",),
            ondelete="CASCADE",
            name="fk_history_logs_type_id_miniature_types",
        ),
    )
    op.create_index(
        "ix_history_logs_type_id_created_at",
        "history_logs",
        ["type_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_history_logs_type_id_created_at", table_name="history_logs")
    op.drop_table("history_logs")
    op.drop_table("stage_counts")
    op.drop_table("miniature_types")
