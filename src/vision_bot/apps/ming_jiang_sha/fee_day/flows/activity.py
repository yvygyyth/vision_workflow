"""活动领取。"""

from __future__ import annotations

from vision_bot.actions import click, do, move
from vision_bot.apps.ming_jiang_sha.actions import close_popup, go_back
from vision_bot.apps.ming_jiang_sha.flow_helpers import scroll_center
from vision_bot.apps.ming_jiang_sha.paths import FEE_DAY
from vision_bot.runtime.result import Result

_DIR = f"{FEE_DAY}/actaivity"


def open_entry(ctx) -> Result:
    return do(move().image(f"{_DIR}/huo_dong.png"), click())(ctx.action_ctx())


def bu_gua_wait(ctx) -> Result:
    ctx.sleep(1.0)
    do(move().to(1400, 600).raw(), click())(ctx.action_ctx())
    return Result.success()


def bu_gua_click(ctx) -> Result:
    ctx.sleep(3.0)
    do(move().to(1400, 600).raw(), click())(ctx.action_ctx())
    return Result.success()


def gua_xiang(ctx) -> Result:
    return do(move().image(f"{_DIR}/gua_xiang.png"), click())(ctx.action_ctx())


def scroll(ctx) -> Result:
    return scroll_center(-120, times=5)


def yue_ling(ctx) -> Result:
    return do(move().image(f"{_DIR}/yue_ling.png"), click())(ctx.action_ctx())


def ling_qv(ctx) -> Result:
    return do(move().image(f"{_DIR}/ling_qv.png"), click())(ctx.action_ctx())


def finish(ctx) -> Result:
    go_back()
    return Result.success()


def close_popup_2(ctx) -> Result:
    """2 秒后按 Esc 关闭弹窗。"""
    ctx.sleep(2.0)
    return close_popup()
