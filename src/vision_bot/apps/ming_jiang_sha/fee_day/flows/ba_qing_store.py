"""巴清商店（每日免费）。"""

from __future__ import annotations

from vision_bot.actions import click, do, move
from vision_bot.apps.ming_jiang_sha.actions import step_go_back
from vision_bot.apps.ming_jiang_sha.flow_helpers import scroll_center
from vision_bot.apps.ming_jiang_sha.paths import FEE_DAY
from vision_bot.runtime.result import Result

_DIR = f"{FEE_DAY}/ba_qing_store"


def entry(ctx) -> Result:
    return do(move().image(f"{_DIR}/entry-icon.png"), click())(ctx.action_ctx())


def gold_tab(ctx) -> Result:
    return do(move().image(f"{_DIR}/gold-tab.png"), click())(ctx.action_ctx())


def free_bingli(ctx) -> Result:
    return do(move().image(f"{_DIR}/free-bingli.png"), click())(ctx.action_ctx())


def copper_tab(ctx) -> Result:
    return do(move().image(f"{_DIR}/copper-tab.png"), click())(ctx.action_ctx())


def lingxi_box(ctx) -> Result:
    return do(move().image(f"{_DIR}/lingxi-box.png"), click())(ctx.action_ctx())


def jinlan_tab(ctx) -> Result:
    return do(move().image(f"{_DIR}/jinlan-tab.png"), click())(ctx.action_ctx())


def scroll(ctx) -> Result:
    return scroll_center(-120, times=15)


def finish(ctx) -> Result:
    step_go_back(ctx)
    return Result.success()
