"""妃妃事件。"""

from __future__ import annotations

import logging

from vision_bot.actions import click, do, move
from vision_bot.apps.ming_jiang_sha.actions import module_confirm
from vision_bot.runtime.flow import Flow, StepResult
from vision_bot.runtime.types import BACK_TO_HUB, END, FAIL

logger = logging.getLogger(__name__)

_OPTS = (
    "data/ming_jiang_sha/qian_li_dan_qi/fei_fei/i_help_you.png",
    "data/ming_jiang_sha/qian_li_dan_qi/fei_fei/sleep.png",
    "data/ming_jiang_sha/qian_li_dan_qi/fei_fei/bargaining.png",
)


def _choose(ctx) -> StepResult:
    act = ctx.action_ctx()
    for path in _OPTS:
        hit = act.find(path, timeout=0.8)
        if hit.found and hit.center:
            do(move().to(*hit.center).raw(), click())(act)
            return StepResult.end(BACK_TO_HUB)
    return StepResult.fail("妃妃选项未识别")


def build() -> Flow:
    return Flow(
        id="fei_fei",
        name="妃妃",
        entry="confirm",
        steps={
            "confirm": module_confirm,
            "choose": _choose,
        },
        routes={"confirm": {FAIL: "choose"}},
        on={BACK_TO_HUB: END},
    )
