"""战斗三选一 mod。"""

from __future__ import annotations

import logging
import time

from vision_bot.apps.ming_jiang_sha.actions import click_confirm
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.flows.battle_hub import (
    CHALLENGE,
    CHALLENGE_HELP,
    CHOICE_REGION,
    YI_WAI,
)
from vision_bot.core.input import Mouse
from vision_bot.runtime.context import RunContext
from vision_bot.runtime.relocate import RelocateRule
from vision_bot.runtime.result import Result
from vision_bot.vision import ScreenSnapshot, find, snap

logger = logging.getLogger(__name__)

DETECT: set[str] = {CHALLENGE, CHALLENGE_HELP, YI_WAI}


def _has_challenge(ctx: RunContext) -> bool:
    shot = snap(DETECT, region=CHOICE_REGION)
    return shot.found(CHALLENGE_HELP) or shot.found(CHALLENGE)


def _has_yi_wai(ctx: RunContext) -> bool:
    return snap(DETECT, region=CHOICE_REGION).found(YI_WAI)


relocate: list[RelocateRule] = [
    RelocateRule(when=_has_challenge, then="qldq.battle_hub.pick_battle.choose"),
    RelocateRule(when=_has_yi_wai, then="qldq.battle_hub.pick_battle.choose_yi_wai"),
]


def _click(shot: ScreenSnapshot, path: str, *, label: str, times: int = 1) -> bool:
    c = shot.center(path)
    if not c:
        return False
    Mouse().move(*c).click(clicks=times).sleep(0.2).perform()
    logger.info("pick_battle %s @ %s x%s", label, c, times)
    return True


def choose(ctx) -> Result:
    shot = snap(DETECT, region=CHOICE_REGION)
    if shot.found(CHALLENGE_HELP):
        if not _click(shot, CHALLENGE_HELP, label="help"):
            return Result.fail("点击 help 失败")
    elif shot.found(CHALLENGE):
        if not _click(shot, CHALLENGE, label="challenge"):
            return Result.fail("点击 challenge 失败")
    else:
        return Result.fail("无战斗选项")
    return Result.success(then="qldq.battle_hub.pick_battle.pre_confirm")


def choose_yi_wai(ctx) -> Result:
    """点意外。三选一用裁剪区；战后结算跳转时可能不在裁剪区内，回落全屏。"""
    shot = snap(DETECT, region=CHOICE_REGION)
    clicked = _click(shot, YI_WAI, label="yi_wai", times=2)
    if not clicked:
        hit = find(YI_WAI, timeout=1.5, interval=0.3)
        if not hit.ok or not hit.value.center:
            return Result.fail("点击意外失败")
        cx, cy = hit.value.center
        Mouse().move(cx, cy).click(clicks=2).sleep(0.2).perform()
        logger.info("pick_battle yi_wai (full) @ (%s,%s) x2", cx, cy)

    time.sleep(0.6)
    # 仍在意外页则再点；全屏判断，与 after_settle 一致
    if find(YI_WAI, timeout=0.5).ok:
        return Result.success(then="qldq.battle_hub.pick_battle.choose_yi_wai")
    return Result.success(then="qldq.battle_hub.pick_battle.pre_confirm")


def pre_confirm(ctx) -> Result:
    r = click_confirm()
    if not r.ok:
        return Result.fail(r.message)
    return Result.success(then="qldq.fight")
