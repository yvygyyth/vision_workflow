"""失败/卡死复位：Esc 回首页后再进战（由 goto/call 进入，非正常主路径）。"""

from __future__ import annotations

import logging
import time

from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.flows import enter_pick
from vision_bot.events import press_esc
from vision_bot.runtime.relocate import RelocateRule
from vision_bot.runtime.result import Result

logger = logging.getLogger(__name__)

relocate: list[RelocateRule] = list(enter_pick.relocate)


def esc_home(ctx) -> Result:
    logger.info("home_recovery: Esc×5")
    press_esc(times=5, pause=0.25)
    time.sleep(0.5)
    ctx.goto("qldq.battle_select.enter_pick")
    return Result.success()
