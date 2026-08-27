"""十常侍 mod。"""

from __future__ import annotations

from vision_bot.actions import click, do, move
from vision_bot.apps.ming_jiang_sha.actions import click_confirm
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.signals import snap_found
from vision_bot.perception.snapshot import capture
from vision_bot.runtime.context import RunContext
from vision_bot.runtime.result import Result
from vision_bot.vision import find

_ATTACK = "data/ming_jiang_sha/qian_li_dan_qi/shi_chang_shi/attack.png"


def relocate(ctx: RunContext) -> str | None:
    snap = capture(ctx.registry, ctx.base_dir, {"shi_chang_shi.attack", "fight.cancel"})
    if snap_found(snap, "shi_chang_shi.attack"):
        return "qldq.shi_chang_shi.attack"
    return "qldq.shi_chang_shi.confirm"


def confirm(ctx) -> Result:
    r = click_confirm()
    if not r.ok:
        ctx.goto("qldq.shi_chang_shi.attack")
    return r


def attack(ctx) -> Result:
    result = find(_ATTACK, timeout=0.8)
    if not result.ok or not result.value.center:
        return Result.fail("无 attack")
    for _ in range(5):
        do(move().to(*result.value.center).raw(), click())()
    ctx.goto("qldq.shi_chang_shi.check_cancel")
    return Result.success()


def check_cancel(ctx) -> Result:
    snap = ctx.snap({"fight.cancel"})
    if snap_found(snap, "fight.cancel"):
        r = click_confirm()
        if not r.ok:
            return r
        ctx.goto("qldq.fight")
        return Result.success()
    ctx.goto("qldq.shi_chang_shi.attack")
    return Result.success()
