"""公会店铺。"""

from __future__ import annotations

from vision_bot.actions import click, do, move
from vision_bot.apps.ming_jiang_sha.actions import go_back
from vision_bot.apps.ming_jiang_sha.paths import FEE_DAY
from vision_bot.runtime.result import Result


def open_entry(ctx) -> Result:
    return do(
        move().image(f"{FEE_DAY}/gong_hui/gong-hui-ru-kou.png", f"{FEE_DAY}/gong_hui/gong-hui-ru-kou-2.png").match(timeout=5.0),
        click(),
    )()


def open_store(ctx) -> Result:
    return do(move().image(f"{FEE_DAY}/gong_hui/gong-hui-store.png"), click())()


def wen_ding_ling(ctx) -> Result:
    return do(move().image(f"{FEE_DAY}/gong_hui/wen_ding_ling.png"), click())()


def tian_ming_ling(ctx) -> Result:
    return do(move().image(f"{FEE_DAY}/gong_hui/tian_ming_ling.png"), click())()


def tian_fa_ling(ctx) -> Result:
    return do(move().image(f"{FEE_DAY}/gong_hui/tian_fa_ling.png"), click())()


def jun_ling_zhuang(ctx) -> Result:
    return do(move().image(f"{FEE_DAY}/gong_hui/jun_ling_zhuang.png"), click())()


def finish(ctx) -> Result:
    go_back()
    return Result.success()
