"""战斗三选一 mod。"""

from __future__ import annotations

import logging
import time

from vision_bot.apps.ming_jiang_sha.actions import click_confirm
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.signals import PICK_BATTLE_DETECT
from vision_bot.core.input import Mouse
from vision_bot.perception.snapshot import ScreenSnapshot, capture
from vision_bot.runtime.context import RunContext
from vision_bot.runtime.result import Result

logger = logging.getLogger(__name__)


def detect(snap: ScreenSnapshot, ctx: RunContext | None = None) -> str | None:
    if snap.found("choice.challenge_help"):
        return "qldq.battle_hub.pick_battle.choose"
    if snap.found("choice.challenge"):
        return "qldq.battle_hub.pick_battle.choose"
    if snap.found("choice.yi_wai"):
        return "qldq.battle_hub.pick_battle.choose_yi_wai"
    return None


def relocate(ctx: RunContext) -> str | None:
    snap = capture(ctx.registry, ctx.base_dir, PICK_BATTLE_DETECT)
    return detect(snap, ctx)


def _click(snap, key: str, *, label: str, times: int = 1) -> bool:
    c = snap.center(key)
    if not c:
        return False
    Mouse().move(*c).click(clicks=times).sleep(0.2).perform()
    logger.info("pick_battle %s @ %s x%s", label, c, times)
    return True


def choose(ctx) -> Result:
    snap = ctx.snap(PICK_BATTLE_DETECT)
    if snap.found("choice.challenge_help"):
        if not _click(snap, "choice.challenge_help", label="help"):
            return Result.fail("点击 help 失败")
    elif snap.found("choice.challenge"):
        if not _click(snap, "choice.challenge", label="challenge"):
            return Result.fail("点击 challenge 失败")
    else:
        return Result.fail("无战斗选项")
    ctx.goto("qldq.battle_hub.pick_battle.pre_confirm")
    return Result.success()


def choose_yi_wai(ctx) -> Result:
    snap = ctx.snap(PICK_BATTLE_DETECT)
    if not _click(snap, "choice.yi_wai", label="yi_wai", times=2):
        return Result.fail("点击意外失败")
    time.sleep(0.6)
    snap2 = ctx.snap({"choice.yi_wai"})
    if snap2.found("choice.yi_wai"):
        ctx.goto("qldq.battle_hub.pick_battle.choose_yi_wai")
        return Result.success()
    ctx.goto("qldq.battle_hub.pick_battle.pre_confirm")
    return Result.success()


def pre_confirm(ctx) -> Result:
    r = click_confirm()
    if not r.ok:
        return Result.fail(r.message)
    ctx.goto("qldq.fight")
    return Result.success()
