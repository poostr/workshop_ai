from __future__ import annotations

from enum import StrEnum
from typing import Final


class StageCode(StrEnum):
    IN_BOX = "IN_BOX"
    BUILDING = "BUILDING"
    PRIMING = "PRIMING"
    PAINTING = "PAINTING"
    DONE = "DONE"


STAGES: Final[tuple[str, str, str, str, str]] = tuple(stage.value for stage in StageCode)

FINAL_STAGE: Final[str] = "DONE"
STAGES_SQL_LIST: Final[str] = ", ".join(f"'{stage}'" for stage in STAGES)
STAGE_INDEX: Final[dict[str, int]] = {stage.value: idx for idx, stage in enumerate(StageCode)}


def is_forward_transition(from_stage: StageCode, to_stage: StageCode) -> bool:
    return STAGE_INDEX[to_stage.value] > STAGE_INDEX[from_stage.value]
