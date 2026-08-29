"""活动领取。"""

from __future__ import annotations

import time

from vision_bot.actions import click, do, move
from vision_bot.actions import scroll as scroll_wheel
from vision_bot.apps.ming_jiang_sha.actions import close_popup, go_back
from vision_bot.apps.ming_jiang_sha.paths import FEE_DAY
from vision_bot.runtime.result import Result


def open_entry(ctx) -> Result:
    return do(move().image(f"{FEE_DAY}/actaivity/huo_dong.png"), click())()


def bu_gua_wait(ctx) -> Result:
    time.sleep(1.0)
    do(move().to(1400, 600).raw(), click())()
    return Result.success()


def bu_gua_click(ctx) -> Result:
    time.sleep(3.0)
    do(move().to(1400, 600).raw(), click())()
    return Result.success()


def gua_xiang(ctx) -> Result:
    do(move().to(300, 300).raw(), click())()
    return Result.success()


def scroll(ctx) -> Result:
    return do(move().at("center"), scroll_wheel(-120).times(12))()


def yue_ling(ctx) -> Result:
    return do(move().image(f"{FEE_DAY}/actaivity/yue_ling.png"), click())()


def ling_qv(ctx) -> Result:
    return do(move().image(f"{FEE_DAY}/actaivity/ling_qv.png"), click())()


def finish(ctx) -> Result:
    go_back()
    return Result.success()


def close_popup_2(ctx) -> Result:
    """2 秒后按 Esc 关闭弹窗。"""
    time.sleep(2.0)
    return close_popup()
