"""Esc 回首页后进战。"""

from __future__ import annotations

import logging
import time

from vision_bot.apps.ming_jiang_sha.actions import press_esc
from vision_bot.runtime.flow import Flow, StepResult
from vision_bot.runtime.types import ENTER_BATTLE, END

logger = logging.getLogger(__name__)


def _esc_home(ctx) -> StepResult:
    logger.info("home_recovery: Esc×5")
    press_esc(ctx.action_ctx(), times=5, pause=0.25)
    time.sleep(0.5)
    return StepResult.end(ENTER_BATTLE)


def build() -> Flow:
    return Flow(
        id="home_recovery",
        name="回首页恢复",
        entry="esc_home",
        steps={"esc_home": _esc_home},
        on={ENTER_BATTLE: END},
    )
