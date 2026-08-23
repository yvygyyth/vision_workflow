"""战斗三选一。"""

from __future__ import annotations

import logging
import time

from vision_bot.apps.ming_jiang_sha.actions import click_confirm
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.detect import relocate_pick_battle
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.signals import PICK_BATTLE_DETECT, snap_center, snap_found
from vision_bot.core.input import Mouse
from vision_bot.runtime.flow import Flow, StepResult
from vision_bot.runtime.types import BACK_TO_HUB, END, FIGHT, STILL_HERE

logger = logging.getLogger(__name__)


def _click(snap, key: str, *, label: str, times: int = 1) -> bool:
    c = snap_center(snap, key)
    if not c:
        return False
    Mouse().move(*c).click(clicks=times).sleep(0.2).perform()
    logger.info("pick_battle %s @ %s x%s", label, c, times)
    return True


def _choose(ctx) -> StepResult:
    snap = ctx.snap(PICK_BATTLE_DETECT)
    if snap_found(snap, "choice.challenge_help"):
        if not _click(snap, "choice.challenge_help", label="help"):
            return StepResult.fail("点击 help 失败")
    elif snap_found(snap, "choice.challenge"):
        if not _click(snap, "choice.challenge", label="challenge"):
            return StepResult.fail("点击 challenge 失败")
    else:
        return StepResult.fail("无战斗选项")
    return StepResult.ok(next_id="pre_confirm")


def _choose_yi_wai(ctx) -> StepResult:
    snap = ctx.snap(PICK_BATTLE_DETECT)
    if not _click(snap, "choice.yi_wai", label="yi_wai", times=2):
        return StepResult.fail("点击意外失败")
    time.sleep(0.6)
    snap2 = ctx.snap({"choice.yi_wai"})
    if snap_found(snap2, "choice.yi_wai"):
        return StepResult.ok(outcome=STILL_HERE, next_id="choose_yi_wai")
    return StepResult.ok(next_id="pre_confirm")


def _pre_confirm(ctx) -> StepResult:
    r = click_confirm(ctx.action_ctx())
    if r.failed:
        return StepResult.fail(r.message)
    return StepResult.end(FIGHT)


def build() -> Flow:
    return Flow(
        id="pick_battle",
        name="战斗选择",
        entry="choose",
        relocate=relocate_pick_battle,
        steps={
            "choose": _choose,
            "choose_yi_wai": _choose_yi_wai,
            "pre_confirm": _pre_confirm,
        },
        on={
            FIGHT: END,
            STILL_HERE: "choose_yi_wai",
            BACK_TO_HUB: END,
        },
    )
