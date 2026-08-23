"""巴清商店（每日免费）。"""

from __future__ import annotations

from vision_bot.apps.ming_jiang_sha.actions import (
    step_click_ming_jiang_ce,
    step_click_max,
    step_confirm,
    step_go_back,
    step_space_close,
)
from vision_bot.apps.ming_jiang_sha.flow_helpers import do_click, scroll_center
from vision_bot.apps.ming_jiang_sha.paths import DATA_ROOT
from vision_bot.runtime.flow import Flow, StepResult

_DIR = f"{DATA_ROOT}/ba_qing_store"
DONE = "ba_qing_done"


def _finish(ctx) -> StepResult:
    step_go_back(ctx)
    return StepResult.end(DONE)


def build() -> Flow:
    return Flow(
        id="ba_qing_store",
        name="巴清商店",
        entry="entry_icon",
        steps={
            "entry_icon": lambda ctx: do_click(ctx, f"{_DIR}/entry-icon.png"),
            "gold_tab": lambda ctx: do_click(ctx, f"{_DIR}/gold-tab.png"),
            "free_bingli": lambda ctx: do_click(ctx, f"{_DIR}/free-bingli.png"),
            "buy_0": step_confirm,
            "space_close": step_space_close,
            "copper_tab": lambda ctx: do_click(ctx, f"{_DIR}/copper-tab.png"),
            "lingxi_box": lambda ctx: do_click(ctx, f"{_DIR}/lingxi-box.png"),
            "max": step_click_max,
            "buy_500": step_confirm,
            "space_close2": step_space_close,
            "space_close3": step_space_close,
            "jinlan_tab": lambda ctx: do_click(ctx, f"{_DIR}/jinlan-tab.png"),
            "scroll": lambda ctx: scroll_center(ctx, -120, times=15),
            "ming_jiang_ce": step_click_ming_jiang_ce,
            "buy_200": step_confirm,
            "space_close4": step_space_close,
            "go_back": _finish,
        },
    )
