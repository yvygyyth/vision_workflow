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
from vision_bot.apps.ming_jiang_sha.flow_helpers import click_image, scroll_center
from vision_bot.apps.ming_jiang_sha.paths import DATA_ROOT
from vision_bot.runtime.builders import flow, mod
from vision_bot.runtime.flow import Flow
from vision_bot.runtime.result import Result

_DIR = f"{DATA_ROOT}/zhan_yi_store"


def _open_entry(ctx) -> Result:
    return click_image(f"{_DIR}/entry.png", f"{_DIR}/entry2.png", timeout=5.0)


def _open_store(ctx) -> Result:
    return click_image(f"{_DIR}/zhan-yi-store.png")


def _scroll(ctx) -> Result:
    return scroll_center(-120, times=10)


def _finish(ctx) -> Result:
    step_go_back(ctx)
    return Result.success()


def build() -> Flow:
    return flow(
        "fee_day.zhan_yi_store",
        "战役商店",
        children=[
            mod("fee_day.zhan_yi_store.entry", "打开入口", _open_entry),
            mod("fee_day.zhan_yi_store.open_store", "打开商店", _open_store),
            mod("fee_day.zhan_yi_store.ming_jiang_ce", "名将册", step_click_ming_jiang_ce),
            mod("fee_day.zhan_yi_store.max", "最大", step_click_max),
            mod("fee_day.zhan_yi_store.buy", "购买", step_confirm),
            mod("fee_day.zhan_yi_store.space_close", "关闭弹窗", step_space_close),
            mod("fee_day.zhan_yi_store.scroll", "滚动", _scroll),
            mod("fee_day.zhan_yi_store.ling_xi_box", "灵犀盒", step_click_ling_xi_box),
            mod("fee_day.zhan_yi_store.max2", "最大2", step_click_max),
            mod("fee_day.zhan_yi_store.buy2", "购买2", step_confirm),
            mod("fee_day.zhan_yi_store.space_close2", "关闭弹窗2", step_space_close),
            mod("fee_day.zhan_yi_store.close", "关闭", step_go_back),
            mod("fee_day.zhan_yi_store.return_btn", "返回", _finish),
        ],
    )
