"""诸葛亮事件 mod。"""

from __future__ import annotations

import time

from vision_bot.actions import click, do, move
from vision_bot.apps.ming_jiang_sha.paths import QLDQ
from vision_bot.events import click_match
from vision_bot.runtime.result import Result
from vision_bot.vision import find

_TITLE = f"{QLDQ}/zhu_ge_liang/title.png"
_NEXT = f"{QLDQ}/zhu_ge_liang/next.png"
_POINT = (1900, 700)


def wait_title(ctx) -> Result:
    r = find(_TITLE)
    if not r.ok:
        return Result.fail(r.message or "未找到占星术士标题")
    do(move().to(*_POINT), click())()
    time.sleep(0.8)
    do(move().to(*_POINT), click())()
    return Result.success()


def click_next(ctx) -> Result:
    r = find(_NEXT)
    if not r.ok:
        return Result.fail(r.message or "未找到继续")
    click_match(r.value)
    ctx.goto("qldq.battle_hub")
    return Result.success()
