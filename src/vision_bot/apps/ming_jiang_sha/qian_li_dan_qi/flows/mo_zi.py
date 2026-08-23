"""墨子事件。"""

from __future__ import annotations

import logging
import random

from vision_bot.actions import click, do, move
from vision_bot.apps.ming_jiang_sha.actions import module_confirm
from vision_bot.runtime.flow import Flow, StepResult
from vision_bot.runtime.types import BACK_TO_HUB, END, FAIL

logger = logging.getLogger(__name__)

_OPTS = ((1130, 360), (1130, 630), (1130, 900))


def _click_option(ctx) -> StepResult:
    x, y = random.choice(_OPTS)
    do(move().to(x, y).raw(), click())(ctx.action_ctx())
    return StepResult.end(BACK_TO_HUB)


def build() -> Flow:
    return Flow(
        id="mo_zi",
        name="墨子",
        entry="confirm",
        steps={
            "confirm": module_confirm,
            "click": _click_option,
        },
        routes={"confirm": {FAIL: "click"}},
        on={BACK_TO_HUB: END},
    )
