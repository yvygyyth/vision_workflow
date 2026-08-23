"""八王之乱步骤。"""

from __future__ import annotations

import logging
import time

from vision_bot.actions import click, do, move
from vision_bot.actions.wait import wait_image
from vision_bot.apps.ming_jiang_sha.flow_helpers import do_click
from vision_bot.apps.ming_jiang_sha.paths import BA_WANG, QLDQ
from vision_bot.core.input import Mouse
from vision_bot.core.vision import find_all_images
from vision_bot.runtime.flow import StepResult

logger = logging.getLogger(__name__)

_DIR = BA_WANG
_FIGHT_DIR = f"{QLDQ}/fight"

_ZHUN_BEI = f"{_DIR}/zhun_bei.png"
_UN_ZHUN_BEI = f"{_DIR}/un_zhun+bei.png"
_START = f"{_DIR}/start.png"
_SIX = f"{_DIR}/6.png"
_OK = f"{_DIR}/ok.png"

_SETTING = f"{_FIGHT_DIR}/setting.png"
_AUTO = f"{_FIGHT_DIR}/auto.png"
_CHALLENGE_END = f"{_FIGHT_DIR}/challenge_end.png"
_NEXT_STEP = f"{_FIGHT_DIR}/next_step.png"

_MAX_SIX = 13
_AFTER_SIX_CLICK_SEC = 0.35
_WAIT_INTERVAL_SEC = 1.0
_WAIT_TIMEOUT_SEC = 600.0

IN_BATTLE = "in_battle"


def _probe(ctx, image: str, *, timeout: float = 0.8) -> bool:
    act = ctx.action_ctx()
    hit = wait_image(
        act,
        (image,),
        threshold=0.8,
        timeout=timeout,
        interval=0.3,
        region=None,
        grayscale=None,
    )
    return hit is not None and hit.found


def _setting_visible(ctx, *, timeout: float = 0.8) -> bool:
    return bool(ctx.action_ctx().find(_SETTING, timeout=timeout, threshold=0.8).found)


def detect_role(ctx) -> StepResult:
    if _probe(ctx, _UN_ZHUN_BEI):
        logger.info("detect_role → member_ready")
        return StepResult.ok(outcome="member_ready")
    if _probe(ctx, _ZHUN_BEI):
        logger.info("detect_role → member")
        return StepResult.ok(outcome="member")
    logger.info("detect_role → owner")
    return StepResult.ok(outcome="owner")


def click_ready(ctx) -> StepResult:
    act = ctx.action_ctx()
    hit = wait_image(
        act,
        (_ZHUN_BEI,),
        threshold=0.8,
        timeout=1.5,
        interval=0.3,
        region=None,
        grayscale=None,
    )
    if hit is None or not hit.center:
        return StepResult.fail("未找到准备按钮")
    cx, cy = hit.center
    logger.info("click_ready @ (%s,%s)", cx, cy)
    Mouse().move(cx, cy).click().sleep(0.2).perform()
    return StepResult.ok()


def confirm_ready(ctx) -> StepResult:
    ctx.sleep(0.5)
    if _probe(ctx, _UN_ZHUN_BEI, timeout=1.0):
        logger.info("confirm_ready → ok")
        return StepResult.ok()
    if _probe(ctx, _ZHUN_BEI, timeout=0.5):
        logger.info("confirm_ready → still_ready")
        return StepResult.ok(outcome="still_ready")
    return StepResult.fail("点击准备后未识别到取消准备")


def poll_click_start(ctx) -> StepResult:
    act = ctx.action_ctx()
    outcome = do(
        move().image(_START).match(timeout=600, interval=1.5),
        click().pause(0.3),
    )(act)
    if not outcome.ok:
        return StepResult.fail(act.reason or "未找到开始按钮")
    return StepResult.ok()


def wait_game_start(ctx) -> StepResult:
    deadline = time.monotonic() + _WAIT_TIMEOUT_SEC
    act = ctx.action_ctx()
    while time.monotonic() < deadline:
        if find_all_images(act.resolve(_SIX), threshold=0.8, max_count=1):
            logger.info("wait_game_start → pick_six")
            return StepResult.ok()
        if _setting_visible(ctx, timeout=0.3):
            logger.info("wait_game_start → in_battle")
            return StepResult.ok(outcome=IN_BATTLE)
        ctx.sleep(_WAIT_INTERVAL_SEC)
    return StepResult.fail("等待开局超时")


def pick_all_sixes(ctx) -> StepResult:
    act = ctx.action_ctx()
    hits = find_all_images(act.resolve(_SIX), threshold=0.8, max_count=_MAX_SIX)
    sorted_hits = sorted(
        (hit for hit in hits if hit.center),
        key=lambda hit: (hit.center[1], hit.center[0]),
    )
    for hit in sorted_hits:
        cx, cy = hit.center
        assert cx is not None and cy is not None
        logger.info("pick_all_sixes @ (%s,%s) conf=%.3f", cx, cy, hit.confidence)
        Mouse().move(cx, cy).click().sleep(0.2).perform()
        ctx.sleep(_AFTER_SIX_CLICK_SEC)
    return StepResult.ok()


def click_ok_if_any(ctx) -> StepResult:
    act = ctx.action_ctx()
    hit = act.find(_OK, timeout=1.0, threshold=0.8)
    if hit.found and hit.center:
        cx, cy = hit.center
        logger.info("click_ok_if_any @ (%s,%s)", cx, cy)
        Mouse().move(cx, cy).click().sleep(0.2).perform()
    return StepResult.ok()


def move_aside(ctx) -> StepResult:
    do(move().to(80, 80).raw())(ctx.action_ctx())
    return StepResult.ok()


def wait_click_setting(ctx) -> StepResult:
    act = ctx.action_ctx()
    outcome = do(
        move().image(_SETTING).match(timeout=600, interval=0.5),
        click().pause(0.3),
    )(act)
    if not outcome.ok:
        return StepResult.fail(act.reason or "未找到 setting")
    return StepResult.ok()


def click_auto(ctx) -> StepResult:
    return do_click(ctx, _AUTO, timeout=3.0)


def click_challenge_end(ctx) -> StepResult:
    act = ctx.action_ctx()
    outcome = do(
        move().image(_CHALLENGE_END).match(timeout=1200, interval=5),
        click(),
    )(act)
    if not outcome.ok:
        return StepResult.fail(act.reason or "挑战未结束")
    return StepResult.ok()


def click_next_step_if_any(ctx) -> StepResult:
    act = ctx.action_ctx()
    for _ in range(5):
        hit = act.find(_NEXT_STEP, timeout=1.2, threshold=0.8)
        if not hit.found or not hit.center:
            break
        cx, cy = hit.center
        logger.info("click_next_step_if_any @ (%s,%s)", cx, cy)
        do(move().to(cx, cy).raw(), click())(act)
        ctx.sleep(0.4)
    return StepResult.ok()


def battle_round_done(ctx) -> StepResult:
    logger.info("battle_round_done → detect_role")
    return StepResult.ok(next_id="detect_role")
