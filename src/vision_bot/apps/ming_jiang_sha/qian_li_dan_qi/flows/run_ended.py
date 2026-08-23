"""本轮结束。"""

from __future__ import annotations

from vision_bot.apps.ming_jiang_sha.actions import module_confirm, module_esc
from vision_bot.runtime.flow import Flow, StepResult
from vision_bot.runtime.types import END, ENTER_BATTLE, FAIL


def _close(ctx) -> StepResult:
    module_esc(ctx, times=2)
    return StepResult.end(ENTER_BATTLE)


def build() -> Flow:
    return Flow(
        id="run_ended",
        name="本轮结束",
        entry="confirm",
        steps={
            "confirm": module_confirm,
            "close": _close,
        },
        routes={"confirm": {FAIL: "close"}},
        on={ENTER_BATTLE: END},
    )
