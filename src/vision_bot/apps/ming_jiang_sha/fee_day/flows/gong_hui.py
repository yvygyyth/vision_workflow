"""公会店铺。"""

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

_DIR = f"{DATA_ROOT}/gong_hui"
DONE = "gong_hui_done"


def _finish(ctx) -> StepResult:
    step_go_back(ctx)
    return StepResult.end(DONE)


def build() -> Flow:
    return Flow(
        id="gong_hui_store",
        name="公会店铺",
        entry="entry",
        steps={
            "entry": lambda ctx: do_click(
                ctx,
                f"{_DIR}/gong-hui-ru-kou.png",
                f"{_DIR}/gong-hui-ru-kou-2.png",
                timeout=5.0,
            ),
            "open_store": lambda ctx: do_click(ctx, f"{_DIR}/gong-hui-store.png"),
            "ming_jiang_ce": step_click_ming_jiang_ce,
            "max": step_click_max,
            "buy": step_confirm,
            "space_close": step_space_close,
            "ling_xi_box": step_click_ling_xi_box,
            "max2": step_click_max,
            "buy2": step_confirm,
            "space_close2": step_space_close,
            "wen_ding_ling": lambda ctx: do_click(ctx, f"{_DIR}/wen_ding_ling.png"),
            "max3": step_click_max,
            "buy3": step_confirm,
            "space_close3": step_space_close,
            "tian_ming_ling": lambda ctx: do_click(ctx, f"{_DIR}/tian_ming_ling.png"),
            "max4": step_click_max,
            "buy4": step_confirm,
            "space_close4": step_space_close,
            "tian_fa_ling": lambda ctx: do_click(ctx, f"{_DIR}/tian_fa_ling.png"),
            "max5": step_click_max,
            "buy5": step_confirm,
            "space_close5": step_space_close,
            "jun_ling_zhuang": lambda ctx: do_click(ctx, f"{_DIR}/jun_ling_zhuang.png"),
            "max6": step_click_max,
            "buy6": step_confirm,
            "space_close6": step_space_close,
            "close": step_go_back,
            "return_btn": _finish,
        },
    )
