"""休息 mod。"""

from __future__ import annotations

import logging
import random

from vision_bot.actions import click, do, move
from vision_bot.runtime.context import RunContext
from vision_bot.runtime.result import Result

logger = logging.getLogger(__name__)

_POINTS = ((110, 1100), (960, 1100), (1800, 1100))


def click_slot(ctx: RunContext) -> Result:
    x, y = random.choice(_POINTS)
    logger.info("rest @ (%s,%s)", x, y)
    do(move().to(x, y).raw(), click())()
    ctx.goto("qldq.battle_hub")
