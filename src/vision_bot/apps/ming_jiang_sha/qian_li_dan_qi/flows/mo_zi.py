"""墨子 mod。"""

from __future__ import annotations

import random

from vision_bot.actions import click, do, move
from vision_bot.apps.ming_jiang_sha.actions import click_confirm
from vision_bot.runtime.result import Result

_OPTS = ((1130, 360), (1130, 630), (1130, 900))


def confirm(ctx) -> Result:
    r = click_confirm()
    if not r.ok:
        ctx.goto("qldq.mo_zi.click")
    return r


def click_option(ctx) -> Result:
    x, y = random.choice(_OPTS)
    do(move().to(x, y).raw(), click())()
    return Result.success()
