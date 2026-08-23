"""休息。"""

from __future__ import annotations

import logging
import random

from vision_bot.actions import click, do, move
from vision_bot.runtime.flow import Flow, StepResult
from vision_bot.runtime.types import BACK_TO_HUB, END

logger = logging.getLogger(__name__)

_POINTS = ((110, 1100), (960, 1100), (1800, 1100))


def _click_slot(ctx) -> StepResult:
    x, y = random.choice(_POINTS)
    logger.info("rest @ (%s,%s)", x, y)
    do(move().to(x, y).raw(), click())(ctx.action_ctx())
    return StepResult.end(BACK_TO_HUB)


def build() -> Flow:
    return Flow(
        id="rest",
        name="休息",
        entry="click_slot",
        steps={"click_slot": _click_slot},
        on={BACK_TO_HUB: END},
    )
