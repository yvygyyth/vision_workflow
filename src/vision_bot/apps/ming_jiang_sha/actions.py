"""公共 UI 动作。"""

from __future__ import annotations

import logging

from vision_bot.actions import click, do, move
from vision_bot.actions.context import ActionContext
from vision_bot.apps.ming_jiang_sha.flow_helpers import do_click
from vision_bot.apps.ming_jiang_sha.paths import COMMON_DIR
from vision_bot.core.input import press_key
from vision_bot.runtime.flow import StepResult

logger = logging.getLogger(__name__)

_CONFIRM = f"{COMMON_DIR}/confirm.png"
_CONFIRM_BELOW_PX = 10
_MAX = f"{COMMON_DIR}/max.png"
_MING_JIANG_CE = f"{COMMON_DIR}/ming_jiang_ce.png"
_LING_XI_BOX = f"{COMMON_DIR}/ling_xi-box.png"


def click_confirm(ctx: ActionContext, *, pause: float = 0.2) -> StepResult:
    hit = ctx.find(_CONFIRM, timeout=3.0, threshold=0.6)
    if not hit.found or not hit.box:
        return StepResult.fail("未找到 confirm")
    x, y, w, h = hit.box
    cx, cy = x + w // 2, y + h + _CONFIRM_BELOW_PX
    logger.info("click_confirm @ (%s,%s)", cx, cy)
    from vision_bot.core.input import Mouse

    Mouse().move(cx, cy).click().sleep(pause).perform()
    return StepResult.ok()


def press_esc(ctx: ActionContext, *, times: int = 1, pause: float = 0.2) -> StepResult:
    from vision_bot.runtime.cancel import raise_if_cancelled, sleep_interruptible

    for _ in range(times):
        raise_if_cancelled(ctx.cancelled)
        press_key("esc")
        sleep_interruptible(ctx.cancelled, pause)
    return StepResult.ok()


def module_confirm(ctx) -> StepResult:
    r = click_confirm(ctx.action_ctx())
    return r if r.failed else StepResult.ok()


def module_esc(ctx, *, times: int = 1) -> StepResult:
    press_esc(ctx.action_ctx(), times=times)
    return StepResult.ok()


def step_confirm(ctx) -> StepResult:
    r = click_confirm(ctx.action_ctx())
    return r if r.failed else StepResult.ok()


def step_space_close(ctx) -> StepResult:
    press_esc(ctx.action_ctx())
    return StepResult.ok()


def step_go_back(ctx, *, times: int = 1) -> StepResult:
    press_esc(ctx.action_ctx(), times=times)
    return StepResult.ok()


def step_click_max(ctx) -> StepResult:
    return do_click(ctx, _MAX)


def step_click_ming_jiang_ce(ctx) -> StepResult:
    return do_click(ctx, _MING_JIANG_CE)


def step_click_ling_xi_box(ctx) -> StepResult:
    return do_click(ctx, _LING_XI_BOX)
