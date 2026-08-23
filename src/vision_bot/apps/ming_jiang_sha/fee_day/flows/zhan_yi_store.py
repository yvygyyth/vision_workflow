"""战役商店。"""

from __future__ import annotations

from vision_bot.apps.ming_jiang_sha.actions import (
    step_click_ling_xi_box,
    step_click_ming_jiang_ce,
    step_click_max,
    step_confirm,
    step_go_back,
    step_space_close,
)
from vision_bot.apps.ming_jiang_sha.flow_helpers import do_click, scroll_center
from vision_bot.apps.ming_jiang_sha.paths import DATA_ROOT
from vision_bot.runtime.flow import Flow, StepResult

_DIR = f"{DATA_ROOT}/zhan_yi_store"
DONE = "zhan_yi_done"


def _finish(ctx) -> StepResult:
    step_go_back(ctx)
    return StepResult.end(DONE)


def build() -> Flow:
    return Flow(
        id="zhan_yi_store",
        name="战役商店",
        entry="entry",
        steps={
            "entry": lambda ctx: do_click(
                ctx, f"{_DIR}/entry.png", f"{_DIR}/entry2.png", timeout=5.0
            ),
            "open_store": lambda ctx: do_click(ctx, f"{_DIR}/zhan_yi-store.png"),
            "ming_jiang_ce": step_click_ming_jiang_ce,
            "max": step_click_max,
            "buy": step_confirm,
            "space_close": step_space_close,
            "scroll": lambda ctx: scroll_center(ctx, -120, times=10),
            "ling_xi_box": step_click_ling_xi_box,
            "max2": step_click_max,
            "buy2": step_confirm,
            "space_close2": step_space_close,
            "close": step_go_back,
            "return_btn": _finish,
        },
    )
