"""战斗与结算（无战前 confirm）。"""

from __future__ import annotations

import logging

from vision_bot.actions import do, move
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.detect import relocate_fight
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.signals import snap_center
from vision_bot.core.input import Mouse
from vision_bot.events import click_match
from vision_bot.runtime.builders import flow, mod
from vision_bot.runtime.flow import Flow
from vision_bot.runtime.result import Result
from vision_bot.vision import find

logger = logging.getLogger(__name__)

_AUTO = "data/ming_jiang_sha/qian_li_dan_qi/fight/auto.png"
_CHALLENGE_END = "data/ming_jiang_sha/qian_li_dan_qi/fight/challenge_end.png"
_NEXT_STEP = "data/ming_jiang_sha/qian_li_dan_qi/fight/next_step.png"


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
    result = find(_AUTO, timeout=1.0)
    if not result.ok:
        return Result.fail("无 auto")
    return click_match(result.value, pause=0.2)


def _wait_end(ctx) -> Result:
    result = find(_CHALLENGE_END, timeout=1200, interval=5)
    if not result.ok:
        return Result.fail("挑战未结束")
    return click_match(result.value, pause=0.2)


def _next_step(ctx) -> Result:
    for _ in range(5):
        result = find(_NEXT_STEP, timeout=1.2)
        if not result.ok or not result.value.center:
            break
        click_match(result.value, pause=0.4)
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
