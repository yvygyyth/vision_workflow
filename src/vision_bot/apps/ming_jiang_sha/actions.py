"""公共 UI 动作。"""

from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path

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


def click_confirm(
    *,
    base_dir: Path,
    cancelled: Callable[[], bool] | None = None,
    pause: float = 0.2,
) -> Result:
    result = find(
        _CONFIRM,
        base_dir=base_dir,
        cancelled=cancelled,
        timeout=3.0,
        threshold=0.6,
    )
    if not result.ok:
        return result
    hit = result.value
    logger.info("click_confirm @ box=%s", hit.box)
    return click_below_box(hit, offset_y=_CONFIRM_BELOW_PX, pause=pause)


def step_confirm(ctx) -> Result:
    return click_confirm(base_dir=ctx.base_dir, cancelled=ctx.cancelled)


def step_space_close(ctx) -> Result:
    return press_esc(cancelled=ctx.cancelled)


def step_go_back(ctx, *, times: int = 1) -> Result:
    return press_esc(cancelled=ctx.cancelled, times=times)


def step_click_max(ctx) -> Result:
    return do_click(ctx, _MAX)


def step_click_ming_jiang_ce(ctx) -> Result:
    return do_click(ctx, _MING_JIANG_CE)


def step_click_ling_xi_box(ctx) -> Result:
    return do_click(ctx, _LING_XI_BOX)
