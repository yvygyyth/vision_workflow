"""煮酒店铺。"""

from __future__ import annotations

from vision_bot.apps.ming_jiang_sha.actions import (
    step_click_ling_xi_box,
    step_click_ming_jiang_ce,
    step_click_max,
    step_confirm,
    step_go_back,
    step_space_close,
)
from vision_bot.apps.ming_jiang_sha.flow_helpers import do_click
from vision_bot.apps.ming_jiang_sha.paths import DATA_ROOT
from vision_bot.runtime.flow import Flow, StepResult

_DIR = f"{DATA_ROOT}/zhu_jiu_store"
DONE = "zhu_jiu_done"


def _finish(ctx) -> StepResult:
    step_go_back(ctx)
    return StepResult.end(DONE)


def build() -> Flow:
    return Flow(
        id="zhu_jiu_store",
        name="煮酒店铺",
        entry="entry",
        steps={
            "entry": lambda ctx: do_click(ctx, f"{_DIR}/entry.png"),
            "qing_mei_store": lambda ctx: do_click(ctx, f"{_DIR}/qing_mei-store.png"),
            "ming_jiang_ce": step_click_ming_jiang_ce,
            "buy": step_confirm,
            "space_close": step_space_close,
            "ling_xi_box": step_click_ling_xi_box,
            "max": step_click_max,
            "buy2": step_confirm,
            "space_close2": step_space_close,
            "close": step_go_back,
            "return_btn": _finish,
        },
    )
