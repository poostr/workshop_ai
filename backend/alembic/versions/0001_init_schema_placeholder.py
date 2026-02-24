"""Initial Alembic revision placeholder.

Revision ID: 0001_init_schema_placeholder
Revises:
Create Date: 2026-02-24 00:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "0001_init_schema_placeholder"
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    # INIT-004 wires migration infrastructure; schema migrations come in DB-001/DB-002.
    pass


def downgrade() -> None:
    pass
