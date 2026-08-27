"""已选将 mod 与画面重定位。"""

from __future__ import annotations

import time

from vision_bot.actions import click, do, move
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.signals import ENTER_DETECT, snap_center, snap_found
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.state import bind_battle_state
from vision_bot.core.input import Mouse, press_key
from vision_bot.perception.snapshot import ScreenSnapshot, capture
from vision_bot.runtime.context import RunContext
from vision_bot.runtime.result import Result


def detect(snap: ScreenSnapshot, ctx: RunContext | None = None) -> str | None:
    if snap_found(snap, "enter.battle_interface"):
        return "qldq.battle_select.enter_ready.check_done"
    if snap_found(snap, "enter.start"):
        return "qldq.battle_select.enter_ready.try_start"
    return "qldq.battle_select.enter_ready.try_start"


def relocate(ctx: RunContext) -> str | None:
    snap = capture(ctx.registry, ctx.base_dir, ENTER_DETECT)
    return detect(snap, ctx)


def check_done(ctx) -> Result:
    bind_battle_state(ctx)
    snap = ctx.snap(ENTER_DETECT)
    if snap_found(snap, "enter.battle_interface"):
        ctx.goto("qldq.battle_hub")
        return Result.success()
    return Result.fail("未进战")


def try_start(ctx) -> Result:
    snap = ctx.snap({"enter.start"})
    c = snap_center(snap, "enter.start")
    if c is None:
        ctx.goto("qldq.battle_select.enter_ready.recover")
        return Result.success()
    Mouse().move(*c).click().sleep(0.5).perform()
    ctx.goto("qldq.battle_select.enter_ready.check_done")
    return Result.success()


def recover(ctx) -> Result:
    for _ in range(3):
        press_key("esc")
        time.sleep(0.2)
    do(move().to(1980, 700).raw(), click())()
    time.sleep(0.2)
    do(move().to(1130, 700).raw(), click())()
    ctx.goto("qldq.battle_select.enter_ready.try_start")
    return Result.success()
