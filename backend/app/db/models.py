from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.domain.stages import STAGES_SQL_LIST


class MiniatureType(Base):
    __tablename__ = "miniature_types"
    __table_args__ = (UniqueConstraint("name", name="uq_miniature_types_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)


class StageCount(Base):
    __tablename__ = "stage_counts"
    __table_args__ = (
        UniqueConstraint("type_id", "stage_name", name="uq_stage_counts_type_stage"),
        CheckConstraint("count >= 0", name="ck_stage_counts_count_non_negative"),
        CheckConstraint(
            f"stage_name IN ({STAGES_SQL_LIST})",
            name="ck_stage_counts_stage_name_valid",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    type_id: Mapped[int] = mapped_column(
        ForeignKey("miniature_types.id", ondelete="CASCADE"),
        nullable=False,
    )
    stage_name: Mapped[str] = mapped_column(String(32), nullable=False)
    count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")


class HistoryLog(Base):
    __tablename__ = "history_logs"
    __table_args__ = (
        Index("ix_history_logs_type_id_created_at", "type_id", "created_at"),
        CheckConstraint(
            f"from_stage IN ({STAGES_SQL_LIST})", name="ck_history_logs_from_stage_valid"
        ),
        CheckConstraint(f"to_stage IN ({STAGES_SQL_LIST})", name="ck_history_logs_to_stage_valid"),
        CheckConstraint("qty > 0", name="ck_history_logs_qty_positive"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    type_id: Mapped[int] = mapped_column(
        ForeignKey("miniature_types.id", ondelete="CASCADE"),
        nullable=False,
    )
    from_stage: Mapped[str] = mapped_column(String(32), nullable=False)
    to_stage: Mapped[str] = mapped_column(String(32), nullable=False)
    qty: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
