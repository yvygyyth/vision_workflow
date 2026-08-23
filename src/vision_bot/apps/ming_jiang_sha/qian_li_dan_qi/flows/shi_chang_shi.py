"""十常侍 → confirm 后进战斗。"""

from __future__ import annotations

import logging

from vision_bot.actions import click, do, move
from vision_bot.apps.ming_jiang_sha.actions import click_confirm, step_confirm
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.detect import qmod, relocate_shi_chang_shi
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.signals import snap_found
from vision_bot.runtime.builders import flow, mod
from vision_bot.runtime.flow import Flow
from vision_bot.runtime.result import Result

logger = logging.getLogger(__name__)


def _confirm(ctx) -> Result:
    r = step_confirm(ctx)
    if r.failed:
        ctx.goto(qmod("shi_chang_shi", "attack"))
    return r


def _attack(ctx) -> Result:
    act = ctx.action_ctx()
    hit = act.find("data/ming_jiang_sha/qian_li_dan_qi/shi_chang_shi/attack.png", timeout=0.8)
    if hit.found and hit.center:
        for _ in range(5):
            do(move().to(*hit.center).raw(), click())(act)
        ctx.goto(qmod("shi_chang_shi", "check_cancel"))
        return Result.success()
    return Result.fail("无 attack")


def _check_cancel(ctx) -> Result:
    snap = ctx.snap({"fight.cancel"})
    if snap_found(snap, "fight.cancel"):
        r = click_confirm(ctx.action_ctx())
        if r.failed:
            return Result.fail(r.message)
        ctx.goto("qldq.fight")
        return Result.success()
    ctx.goto(qmod("shi_chang_shi", "attack"))
    return Result.success()


def build() -> Flow:
    return flow(
        "qldq.shi_chang_shi",
        "十常侍",
        children=[
            mod("qldq.shi_chang_shi.confirm", "确认", _confirm),
            mod("qldq.shi_chang_shi.attack", "攻击", _attack),
            mod("qldq.shi_chang_shi.check_cancel", "检查取消", _check_cancel),
        ],
        relocate=[relocate_shi_chang_shi],
    )
