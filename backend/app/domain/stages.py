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
