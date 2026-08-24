"""公共 UI 动作。"""

from __future__ import annotations

import logging

from vision_bot.actions import click, do, move
from vision_bot.apps.ming_jiang_sha.paths import COMMON_DIR, BA_WANG
from vision_bot.events import click_below_box, press_esc
from vision_bot.runtime.result import Result
from vision_bot.vision import find

logger = logging.getLogger(__name__)

_CONFIRM = f"{COMMON_DIR}/confirm.png"
_CONFIRM_BELOW_PX = 10
_MAX = f"{COMMON_DIR}/max.png"
_MING_JIANG_CE = f"{BA_WANG}/ming_jiang_ce.png"
_LING_XI_BOX = f"{COMMON_DIR}/ling_xi-box.png"


def click_confirm(*, pause: float = 0.2) -> Result:
    """识图 confirm 按钮并点击其下方区域。"""
    result = find(_CONFIRM, timeout=3.0, threshold=0.6)
    if not result.ok:
        return result
    hit = result.value
    logger.info("click_confirm @ box=%s", hit.box)
    return click_below_box(hit, offset_y=_CONFIRM_BELOW_PX, pause=pause)


def step_confirm(ctx) -> Result:
    """Flow 步骤：点击 confirm。"""
    return click_confirm()


def step_space_close(ctx) -> Result:
    """Flow 步骤：按 Esc 关闭弹窗。"""
    return press_esc()


def step_go_back(ctx, *, times: int = 1) -> Result:
    """Flow 步骤：按 Esc 返回。"""
    return press_esc(times=times)


def step_click_max(ctx) -> Result:
    """Flow 步骤：点击 max 按钮。"""
    return do(move().image(_MAX), click())(ctx.action_ctx())


def step_click_ming_jiang_ce(ctx) -> Result:
    """Flow 步骤：点击名将册。"""
    return do(move().image(_MING_JIANG_CE), click())(ctx.action_ctx())


def step_click_ling_xi_box(ctx) -> Result:
    """Flow 步骤：点击灵犀盒。"""
    return do(move().image(_LING_XI_BOX), click())(ctx.action_ctx())
