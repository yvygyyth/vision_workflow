"""巴清商店 mod。"""

from __future__ import annotations

import time

from vision_bot.actions import click, do, move
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.ids import qmod
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.signals import ensure_registry, snap_found
from vision_bot.perception.snapshot import capture
from vision_bot.runtime.context import RunContext
from vision_bot.runtime.result import Result


def relocate(ctx: RunContext) -> str | None:
    ensure_registry(ctx)
    snap = capture(ctx.registry, ctx.base_dir, {"shop.go_back"})
    if snap_found(snap, "shop.go_back"):
        return qmod("ba_qing_store", "go_back")
    return None


def go_back(ctx) -> Result:
    do(move().image("data/ming_jiang_sha/qian_li_dan_qi/ba_qing_store/go_back.png"), click())(
        ctx.action_ctx()
    )
    return Result.success()


def confirm(ctx) -> Result:
    do(move().image("data/ming_jiang_sha/qian_li_dan_qi/ba_qing_store/confirm.png"), click())(
        ctx.action_ctx()
    )
    return Result.success()


def ensure_left(ctx) -> Result:
    time.sleep(0.6)
    snap = ctx.snap({"shop.go_back"})
    if snap_found(snap, "shop.go_back"):
        return Result.fail("仍在店内")
    return Result.success()
