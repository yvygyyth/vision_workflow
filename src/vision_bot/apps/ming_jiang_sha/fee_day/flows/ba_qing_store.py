"""巴清商店（每日免费）。"""

from __future__ import annotations

from vision_bot.actions import click, do, move
from vision_bot.apps.ming_jiang_sha.actions import go_back
from vision_bot.apps.ming_jiang_sha.flow_helpers import scroll_center
from vision_bot.apps.ming_jiang_sha.paths import FEE_DAY
from vision_bot.runtime.result import Result


def entry(ctx) -> Result:
    return do(move().image(f"{FEE_DAY}/ba_qing_store/entry-icon.png"), click())()


def gold_tab(ctx) -> Result:
    return do(move().image(f"{FEE_DAY}/ba_qing_store/gold-tab.png"), click())()


def free_bingli(ctx) -> Result:
    return do(move().image(f"{FEE_DAY}/ba_qing_store/free-bingli.png"), click())()


def copper_tab(ctx) -> Result:
    return do(move().image(f"{FEE_DAY}/ba_qing_store/copper-tab.png"), click())()


def lingxi_box(ctx) -> Result:
    return do(move().image(f"{FEE_DAY}/ba_qing_store/lingxi-box.png"), click())()


def jinlan_tab(ctx) -> Result:
    return do(move().image(f"{FEE_DAY}/ba_qing_store/jinlan-tab.png"), click())()


def scroll(ctx) -> Result:
    return scroll_center(-120, times=15)


def finish(ctx) -> Result:
    go_back()
    return Result.success()
