"""三选一枢纽 mod。"""

from __future__ import annotations

import time

from vision_bot.actions import click, do, move
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.signals import snap_found
from vision_bot.runtime.result import Result


def dismiss_up(ctx) -> Result:
    snap = ctx.snap({"choice.up_panel"})
    if snap_found(snap, "choice.up_panel"):
        do(move().to(1300, 1150).raw(), click())(ctx.action_ctx())
        time.sleep(0.4)
    return Result.fail("dispatch")
