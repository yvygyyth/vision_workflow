"""Esc 回首页后进战。"""

from __future__ import annotations

import logging
import time

from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.signals import ensure_registry
from vision_bot.events import press_esc
from vision_bot.runtime.result import Result

logger = logging.getLogger(__name__)


def esc_home(ctx) -> Result:
    logger.info("home_recovery: Esc×5")
    ensure_registry(ctx)
    press_esc(times=5, pause=0.25)
    time.sleep(0.5)
    ctx.goto("qldq.battle_select.enter_ready")
    return Result.success()
