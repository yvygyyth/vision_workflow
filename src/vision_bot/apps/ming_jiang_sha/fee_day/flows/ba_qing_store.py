"""巴清商店（每日免费）。"""

from __future__ import annotations

from vision_bot.apps.ming_jiang_sha.actions import (
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

_DIR = f"{DATA_ROOT}/ba_qing_store"


def _entry(ctx) -> Result:
    return click_image(f"{_DIR}/entry-icon.png")


def _gold_tab(ctx) -> Result:
    return click_image(f"{_DIR}/gold-tab.png")


def _free_bingli(ctx) -> Result:
    return click_image(f"{_DIR}/free-bingli.png")


def _copper_tab(ctx) -> Result:
    return click_image(f"{_DIR}/copper-tab.png")


def _lingxi_box(ctx) -> Result:
    return click_image(f"{_DIR}/lingxi-box.png")


def _jinlan_tab(ctx) -> Result:
    return click_image(f"{_DIR}/jinlan-tab.png")


def _scroll(ctx) -> Result:
    return scroll_center(-120, times=15)


def _finish(ctx) -> Result:
    step_go_back(ctx)
    return Result.success()


def build() -> Flow:
    return flow(
        "fee_day.ba_qing_store",
        "巴清商店",
        children=[
            mod("fee_day.ba_qing_store.entry", "打开入口", _entry),
            mod("fee_day.ba_qing_store.gold_tab", "金币页", _gold_tab),
            mod("fee_day.ba_qing_store.free_bingli", "免费兵力", _free_bingli),
            mod("fee_day.ba_qing_store.buy_0", "购买0", step_confirm),
            mod("fee_day.ba_qing_store.space_close", "关闭弹窗", step_space_close),
            mod("fee_day.ba_qing_store.copper_tab", "铜币页", _copper_tab),
            mod("fee_day.ba_qing_store.lingxi_box", "灵犀盒", _lingxi_box),
            mod("fee_day.ba_qing_store.max", "最大", step_click_max),
            mod("fee_day.ba_qing_store.buy_500", "购买500", step_confirm),
            mod("fee_day.ba_qing_store.space_close2", "关闭弹窗2", step_space_close),
            mod("fee_day.ba_qing_store.space_close3", "关闭弹窗3", step_space_close),
            mod("fee_day.ba_qing_store.jinlan_tab", "金兰页", _jinlan_tab),
            mod("fee_day.ba_qing_store.scroll", "滚动", _scroll),
            mod("fee_day.ba_qing_store.ming_jiang_ce", "名将册", step_click_ming_jiang_ce),
            mod("fee_day.ba_qing_store.buy_200", "购买200", step_confirm),
            mod("fee_day.ba_qing_store.space_close4", "关闭弹窗4", step_space_close),
            mod("fee_day.ba_qing_store.go_back", "返回", _finish),
        ],
    )
