"""八王之乱步骤。"""

from __future__ import annotations

import logging
import time

from vision_bot.actions import click, do, move
from vision_bot.actions.context import action_context
from vision_bot.apps.ming_jiang_sha.paths import BA_WANG, QLDQ
from vision_bot.events import click_at
from vision_bot.runtime.result import Result
from vision_bot.vision import find, find_all

logger = logging.getLogger(__name__)


_ZHUN_BEI = f"{BA_WANG}/zhun_bei.png"
_UN_ZHUN_BEI = f"{BA_WANG}/un_zhun+bei.png"
_START = f"{BA_WANG}/start.png"
_SIX = f"{BA_WANG}/6.png"
_OK = f"{BA_WANG}/ok.png"

_SETTING = f"{QLDQ}/fight/setting.png"
_AUTO = f"{QLDQ}/fight/auto.png"
_CHALLENGE_END = f"{QLDQ}/fight/challenge_end.png"
_NEXT_STEP = f"{QLDQ}/fight/next_step.png"

_MAX_SIX = 13
_AFTER_SIX_CLICK_SEC = 0.35
_WAIT_INTERVAL_SEC = 1.0
_WAIT_TIMEOUT_SEC = 600.0


def _probe(image: str, *, timeout: float = 0.8) -> bool:
    return find(image, timeout=timeout, interval=0.3).ok


def _setting_visible(*, timeout: float = 0.8) -> bool:
    return find(_SETTING, timeout=timeout).ok


def relocate_role(ctx) -> str | None:
    """根据当前界面决定下一轮的入口（房主 / 房客共用）。"""
    if _probe(_ZHUN_BEI):
        logger.info("relocate_role → click_ready")
        return "ba_wang.click_ready"
    # 房客：优先等「开始」；勿因房主已准备（取消准备可见）误进 wait_game_start
    if _probe(_START, timeout=0.5):
        logger.info("relocate_role → poll_start")
        return "ba_wang.poll_start"
    if _probe(_UN_ZHUN_BEI):
        logger.info("relocate_role → wait_game_start")
        return "ba_wang.wait_game_start"
    logger.info("relocate_role → poll_start")
    return "ba_wang.poll_start"


def click_ready(ctx) -> Result:
    result = find(_ZHUN_BEI, timeout=1.5, interval=0.3)
    if not result.ok or not result.value.center:
        return Result.fail("未找到准备按钮")
    cx, cy = result.value.center
    logger.info("click_ready @ (%s,%s)", cx, cy)
    click_at(cx, cy, pause=0.2)
    ctx.goto("ba_wang.confirm_ready")
    return Result.success()


def confirm_ready(ctx) -> Result:
    time.sleep(0.5)
    if _probe(_UN_ZHUN_BEI, timeout=1.0):
        logger.info("confirm_ready → wait_game_start")
        ctx.goto("ba_wang.wait_game_start")
        return Result.success()
    if _probe(_ZHUN_BEI, timeout=0.5):
        logger.info("confirm_ready → click_ready")
        ctx.goto("ba_wang.click_ready")
        return Result.success()
    return Result.fail("点击准备后未识别到取消准备")


def poll_click_start(ctx) -> Result:
    result = do(
        move().image(_START).match(timeout=600, interval=1.5),
        click().pause(0.3),
    )()
    if not result.ok:
        return Result.fail(result.message or action_context().reason or "未找到开始按钮")
    ctx.goto("ba_wang.wait_game_start")
    return Result.success()


def wait_game_start(ctx) -> Result:
    deadline = time.monotonic() + _WAIT_TIMEOUT_SEC
    while time.monotonic() < deadline:
        if find_all(_SIX, max_count=1).ok:
            logger.info("wait_game_start → pick_six")
            ctx.goto("ba_wang.pick_six")
            return Result.success()
        if _setting_visible(timeout=0.3):
            logger.info("wait_game_start → move_aside")
            ctx.goto("ba_wang.move_aside")
            return Result.success()
        time.sleep(_WAIT_INTERVAL_SEC)
    return Result.fail("等待开局超时")


def pick_all_sixes(ctx) -> Result:
    result = find_all(_SIX, max_count=_MAX_SIX)
    if not result.ok:
        return result
    sorted_hits = sorted(
        (hit for hit in result.value if hit.center),
        key=lambda hit: (hit.center[1], hit.center[0]),
    )
    for hit in sorted_hits:
        cx, cy = hit.center
        assert cx is not None and cy is not None
        logger.info("pick_all_sixes @ (%s,%s) conf=%.3f", cx, cy, hit.confidence)
        click_at(cx, cy, pause=0.2)
        time.sleep(_AFTER_SIX_CLICK_SEC)
    ctx.goto("ba_wang.click_ok")
    return Result.success()


def click_ok_if_any(ctx) -> Result:
    result = find(_OK, timeout=1.0)
    if result.ok and result.value.center:
        cx, cy = result.value.center
        logger.info("click_ok_if_any @ (%s,%s)", cx, cy)
        click_at(cx, cy, pause=0.2)
    ctx.goto("ba_wang.move_aside")
    return Result.success()


def move_aside(ctx) -> Result:
    do(move().to(80, 80).raw())()
    ctx.goto("ba_wang.wait_setting")
    return Result.success()


def wait_click_setting(ctx) -> Result:
    result = do(
        move().image(_SETTING).match(timeout=600, interval=0.5),
        click().pause(0.3),
    )()
    if not result.ok:
        return Result.fail(result.message or action_context().reason or "未找到 setting")
    ctx.goto("ba_wang.click_auto")
    return Result.success()


def click_auto(ctx) -> Result:
    r = do(move().image(_AUTO).match(timeout=3.0), click())()
    if not r.ok:
        ctx.goto("ba_wang.wait_setting")
    else:
        ctx.goto("ba_wang.click_challenge_end")
    return Result.success()


def click_challenge_end(ctx) -> Result:
    result = do(
        move().image(_CHALLENGE_END).match(timeout=1200, interval=5),
        click(),
    )()
    if not result.ok:
        return Result.fail(result.message or action_context().reason or "挑战未结束")
    ctx.goto("ba_wang.next_step")
    return Result.success()


def click_next_step_if_any(ctx) -> Result:
    for _ in range(5):
        result = find(_NEXT_STEP, timeout=1.2)
        if not result.ok or not result.value.center:
            break
        cx, cy = result.value.center
        logger.info("click_next_step_if_any @ (%s,%s)", cx, cy)
        do(move().to(cx, cy).raw(), click())()
        time.sleep(0.4)
    ctx.goto("ba_wang.battle_done")
    return Result.success()


def battle_round_done(ctx) -> Result:
    target = relocate_role(ctx)
    logger.info("battle_round_done → call %s", target)
    ctx.call(target)
    return Result.success()
