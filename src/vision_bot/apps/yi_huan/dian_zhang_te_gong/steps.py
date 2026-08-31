"""店长特供步骤。"""

from __future__ import annotations

import logging
import time

from vision_bot.apps.yi_huan.paths import DIAN_ZHANG_TE_GONG
from vision_bot.events import click_at
from vision_bot.runtime.result import Result
from vision_bot.vision import find
from vision_bot.vision.find import ScreenSnapshot

logger = logging.getLogger(__name__)

_START = f"{DIAN_ZHANG_TE_GONG}/start.png"
_START_PRESSED = f"{DIAN_ZHANG_TE_GONG}/start2.png"
_CZ = f"{DIAN_ZHANG_TE_GONG}/cz.png"
_LING_QV = f"{DIAN_ZHANG_TE_GONG}/ling_qv.png"

_TAP_XY = (120, 600)
_CLICK_INTERVAL_SEC = 0.1
_PROBE_INTERVAL_SEC = 2.0
_CLICK_HOLD_SEC = 0.3


def _click_image(*paths: str) -> bool:
    """按给定顺序优先匹配并点击第一张命中的图。"""
    if not paths:
        return False
    if len(paths) == 1:
        hit = find(paths[0], timeout=0.35)
        if not isinstance(hit, Result) or not hit.ok or not hit.value.center:
            return False
        cx, cy = hit.value.center
        click_at(cx, cy, pause=_CLICK_INTERVAL_SEC, hold=_CLICK_HOLD_SEC)
        return True

    snap = find(*paths, timeout=0.35)
    if isinstance(snap, Result):
        if snap.ok and snap.value.center:
            cx, cy = snap.value.center
            click_at(cx, cy, pause=_CLICK_INTERVAL_SEC, hold=_CLICK_HOLD_SEC)
            return True
        return False
    if not isinstance(snap, ScreenSnapshot):
        return False
    for path in paths:
        r = snap.hits.get(path)
        if r is not None and r.ok and r.value.center:
            cx, cy = r.value.center
            click_at(cx, cy, pause=_CLICK_INTERVAL_SEC, hold=_CLICK_HOLD_SEC)
            return True
    return False


def click_start_until_cz(ctx) -> Result:
    """不停点「开始营业」（优先按压态），直到锤图标 cz 出现。"""
    next_probe = 0.0
    while True:
        now = time.monotonic()
        if now >= next_probe:
            if find(_CZ, timeout=0.35).ok:
                logger.info("cz visible → tap_until_claim")
                return Result.success()
            next_probe = time.monotonic() + _PROBE_INTERVAL_SEC

        # 优先识别按压态 start2，再回落到未按压 start
        if not _click_image(_START_PRESSED, _START):
            time.sleep(_CLICK_INTERVAL_SEC)


def tap_until_claim(ctx) -> Result:
    """绝对坐标连点，直到出现领取并点击。cz 仅用于上一阶段确认已进关。"""
    next_probe = 0.0
    while True:
        now = time.monotonic()
        if now >= next_probe:
            hit = find(_LING_QV, timeout=0.35)
            if hit.ok and hit.value.center:
                cx, cy = hit.value.center
                logger.info("claim @ (%s,%s)", cx, cy)
                click_at(cx, cy, pause=0.3, hold=_CLICK_HOLD_SEC)
                return Result.success()
            next_probe = time.monotonic() + _PROBE_INTERVAL_SEC

        click_at(*_TAP_XY, pause=_CLICK_INTERVAL_SEC, hold=_CLICK_HOLD_SEC)
