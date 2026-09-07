"""墨子 mod。"""

from __future__ import annotations

import random

from vision_bot.actions import click, do, move
from vision_bot.runtime.context import RunContext
from vision_bot.runtime.result import Result

_OPTS = ((1130, 360), (1130, 630), (1130, 900))


def click_option(ctx: RunContext) -> Result:
    x, y = random.choice(_OPTS)
    do(move().to(x, y).raw(), click())()
    ctx.goto("qldq.battle_hub")
