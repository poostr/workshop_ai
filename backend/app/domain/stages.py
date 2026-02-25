from __future__ import annotations

from typing import Final

STAGES: Final[tuple[str, str, str, str, str]] = (
    "IN_BOX",
    "BUILDING",
    "PRIMING",
    "PAINTING",
    "DONE",
)

FINAL_STAGE: Final[str] = "DONE"
STAGES_SQL_LIST: Final[str] = ", ".join(f"'{stage}'" for stage in STAGES)
