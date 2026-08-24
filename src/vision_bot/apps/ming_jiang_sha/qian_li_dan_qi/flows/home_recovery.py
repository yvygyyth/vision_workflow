"""Esc 回首页后进战。"""

from __future__ import annotations

import logging
import time

from vision_bot.events import press_esc
from vision_bot.runtime.builders import flow, mod
from vision_bot.runtime.flow import Flow
from vision_bot.runtime.result import Result

logger = logging.getLogger(__name__)


def _esc_home(ctx) -> Result:
    logger.info("home_recovery: Esc×5")
    press_esc(times=5, pause=0.25)
    time.sleep(0.5)
    ctx.goto("qldq.enter_battle")
    return Result.success()


def build() -> Flow:
    return flow(
        "qldq.home_recovery",
        "回首页恢复",
        children=[
            mod("qldq.home_recovery.esc_home", "Esc回首页", _esc_home),
        ],
    )
