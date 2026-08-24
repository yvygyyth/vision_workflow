"""公共 UI 动作。"""

from __future__ import annotations

import logging

from vision_bot.apps.ming_jiang_sha.flow_helpers import do_click
from vision_bot.apps.ming_jiang_sha.paths import COMMON_DIR
from vision_bot.events import click_below_box, press_esc
from vision_bot.runtime.result import Result
from vision_bot.vision import find

logger = logging.getLogger(__name__)

_CONFIRM = f"{COMMON_DIR}/confirm.png"
_CONFIRM_BELOW_PX = 10
_MAX = f"{COMMON_DIR}/max.png"
_MING_JIANG_CE = f"{COMMON_DIR}/ming_jiang_ce.png"
_LING_XI_BOX = f"{COMMON_DIR}/ling_xi-box.png"


def click_confirm(*, pause: float = 0.2) -> Result:
    """识图 confirm 按钮并点击其下方区域。

    Parameters
    ----------
    pause:
        点击后等待秒数，默认 ``0.2``。

    Returns
    -------
    Result
        找到并点击时 ``ok=True``；未找到 confirm 时 ``ok=False``。
    """
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
    """Flow 步骤：按 Esc 返回。

    Parameters
    ----------
    ctx:
        运行上下文（保留以兼容步骤签名，未使用）。
    times:
        连按 Esc 次数，默认 ``1``。
    """
    return press_esc(times=times)


def step_click_max(ctx) -> Result:
    """Flow 步骤：点击 max 按钮。"""
    return do_click(ctx, _MAX)


def step_click_ming_jiang_ce(ctx) -> Result:
    """Flow 步骤：点击名将册。"""
    return do_click(ctx, _MING_JIANG_CE)


def step_click_ling_xi_box(ctx) -> Result:
    """Flow 步骤：点击灵犀盒。"""
    return do_click(ctx, _LING_XI_BOX)
