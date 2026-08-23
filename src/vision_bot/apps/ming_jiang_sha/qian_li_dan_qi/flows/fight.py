"""战斗与结算（无战前 confirm）。"""

from __future__ import annotations

import logging
import time

from vision_bot.actions import click, do, move
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.detect import relocate_fight
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.signals import snap_center
from vision_bot.core.input import Mouse
from vision_bot.runtime.flow import Flow, StepResult
from vision_bot.runtime.types import BACK_TO_HUB, END

logger = logging.getLogger(__name__)


def _move_aside(ctx) -> StepResult:
    do(move().to(80, 80).raw())(ctx.action_ctx())
    return StepResult.ok(next_id="click_cancel")


def _click_cancel(ctx) -> StepResult:
    snap = ctx.snap({"fight.cancel"})
    c = snap_center(snap, "fight.cancel")
    if c:
        Mouse().move(*c).click().sleep(0.2).perform()
        return StepResult.ok(next_id="click_setting")
    return StepResult.fail("无 cancel")


def _click_setting(ctx) -> StepResult:
    snap = ctx.snap({"fight.setting"})
    c = snap_center(snap, "fight.setting")
    if c:
        Mouse().move(*c).click().sleep(0.5).perform()
        return StepResult.ok(next_id="click_auto")
    return StepResult.fail("无 setting")


def _click_auto(ctx) -> StepResult:
    act = ctx.action_ctx()
    hit = act.find("data/ming_jiang_sha/qian_li_dan_qi/fight/auto.png", timeout=1.0)
    if hit.found and hit.center:
        Mouse().move(*hit.center).click().sleep(0.2).perform()
        return StepResult.ok(next_id="wait_end")
    return StepResult.fail("无 auto")


def _wait_end(ctx) -> StepResult:
    act = ctx.action_ctx()
    hit = act.find("data/ming_jiang_sha/qian_li_dan_qi/fight/challenge_end.png", timeout=1200, interval=5)
    if hit.found and hit.center:
        Mouse().move(*hit.center).click().sleep(0.2).perform()
        return StepResult.ok(next_id="next_step")
    return StepResult.fail("挑战未结束")


def _next_step(ctx) -> StepResult:
    for _ in range(5):
        hit = ctx.action_ctx().find("data/ming_jiang_sha/qian_li_dan_qi/fight/next_step.png", timeout=1.2)
        if not (hit.found and hit.center):
            break
        Mouse().move(*hit.center).click().sleep(0.4).perform()
    return StepResult.end(BACK_TO_HUB)


def build() -> Flow:
    return Flow(
        id="fight",
        name="战斗",
        entry="move_aside",
        relocate=relocate_fight,
        steps={
            "move_aside": _move_aside,
            "click_cancel": _click_cancel,
            "click_setting": _click_setting,
            "click_auto": _click_auto,
            "wait_end": _wait_end,
            "next_step": _next_step,
        },
        on={BACK_TO_HUB: END},
    )
