"""休息。"""

from __future__ import annotations

import logging
import random

from vision_bot.actions import click, do, move
from vision_bot.runtime.builders import flow, mod
from vision_bot.runtime.flow import Flow
from vision_bot.runtime.result import Result

logger = logging.getLogger(__name__)

_POINTS = ((110, 1100), (960, 1100), (1800, 1100))


def _click_slot(ctx) -> Result:
    x, y = random.choice(_POINTS)
    logger.info("rest @ (%s,%s)", x, y)
    do(move().to(x, y).raw(), click())(ctx.action_ctx())
    return Result.success()


def build() -> Flow:
    return flow(
        "qldq.rest",
        "休息",
        children=[
            mod("qldq.rest.click_slot", "点休息", _click_slot),
        ],
    )
