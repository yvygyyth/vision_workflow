"""墨子 mod。"""

from __future__ import annotations

import random

from vision_bot.actions import click, do, move
from vision_bot.runtime.result import Result

_OPTS = ((1130, 360), (1130, 630), (1130, 900))


def click_option(ctx) -> Result:
    x, y = random.choice(_OPTS)
    do(move().to(x, y).raw(), click())()
    return Result.success(then="qldq.battle_hub")
