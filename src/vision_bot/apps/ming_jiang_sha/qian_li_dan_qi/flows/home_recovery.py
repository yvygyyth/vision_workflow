"""失败/卡死复位：Esc 回首页后再进战（由 goto/call 进入，非正常主路径）。"""

from __future__ import annotations

import logging
import time

from vision_bot.actions import click, do, move
from vision_bot.events import press_esc
from vision_bot.runtime.result import Result

logger = logging.getLogger(__name__)


def esc_home(ctx) -> Result:
    logger.info("home_recovery: Esc×5")
    press_esc(times=5, pause=0.25)
    time.sleep(0.5)
    logger.info("home_recovery: 点入口 (1970,730) → (1130,700)")
    do(move().to(1970, 730), click())()
    time.sleep(0.5)
    do(move().to(1130, 700), click())()
    return Result.success(then="qldq.battle_select.enter_pick")
