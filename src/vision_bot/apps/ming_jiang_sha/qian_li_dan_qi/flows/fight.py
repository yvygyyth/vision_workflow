"""战斗与结算（无战前 confirm）。"""

from __future__ import annotations

import logging

from vision_bot.actions import click, do, move
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.detect import relocate_fight
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.signals import snap_center
from vision_bot.core.input import Mouse
from vision_bot.runtime.builders import flow, mod
from vision_bot.runtime.flow import Flow
from vision_bot.runtime.result import Result

logger = logging.getLogger(__name__)


def _move_aside(ctx) -> Result:
    do(move().to(80, 80).raw())(ctx.action_ctx())
    return Result.success()


def _click_cancel(ctx) -> Result:
    snap = ctx.snap({"fight.cancel"})
    c = snap_center(snap, "fight.cancel")
    if c:
        Mouse().move(*c).click().sleep(0.2).perform()
        return Result.success()
    return Result.fail("无 cancel")


def _click_setting(ctx) -> Result:
    snap = ctx.snap({"fight.setting"})
    c = snap_center(snap, "fight.setting")
    if c:
        Mouse().move(*c).click().sleep(0.5).perform()
        return Result.success()
    return Result.fail("无 setting")


def _click_auto(ctx) -> Result:
    act = ctx.action_ctx()
    hit = act.find("data/ming_jiang_sha/qian_li_dan_qi/fight/auto.png", timeout=1.0)
    if hit.found and hit.center:
        Mouse().move(*hit.center).click().sleep(0.2).perform()
        return Result.success()
    return Result.fail("无 auto")


def _wait_end(ctx) -> Result:
    act = ctx.action_ctx()
    hit = act.find("data/ming_jiang_sha/qian_li_dan_qi/fight/challenge_end.png", timeout=1200, interval=5)
    if hit.found and hit.center:
        Mouse().move(*hit.center).click().sleep(0.2).perform()
        return Result.success()
    return Result.fail("挑战未结束")


def _next_step(ctx) -> Result:
    for _ in range(5):
        hit = ctx.action_ctx().find("data/ming_jiang_sha/qian_li_dan_qi/fight/next_step.png", timeout=1.2)
        if not (hit.found and hit.center):
            break
        Mouse().move(*hit.center).click().sleep(0.4).perform()
    return Result.success()


def build() -> Flow:
    return flow(
        "qldq.fight",
        "战斗",
        children=[
            mod("qldq.fight.move_aside", "移开鼠标", _move_aside),
            mod("qldq.fight.click_cancel", "点取消", _click_cancel),
            mod("qldq.fight.click_setting", "点设置", _click_setting),
            mod("qldq.fight.click_auto", "点自动", _click_auto),
            mod("qldq.fight.wait_end", "等结束", _wait_end),
            mod("qldq.fight.next_step", "下一步", _next_step),
        ],
        relocate=[relocate_fight],
    )
