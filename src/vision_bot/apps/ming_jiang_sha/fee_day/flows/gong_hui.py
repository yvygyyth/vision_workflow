"""公会店铺。"""

from __future__ import annotations

from vision_bot.actions import click, do, move
from vision_bot.apps.ming_jiang_sha.actions import step_go_back
from vision_bot.apps.ming_jiang_sha.paths import FEE_DAY
from vision_bot.runtime.result import Result

_DIR = f"{FEE_DAY}/gong_hui"


def open_entry(ctx) -> Result:
    return do(
        move().image(f"{_DIR}/gong-hui-ru-kou.png", f"{_DIR}/gong-hui-ru-kou-2.png").match(timeout=5.0),
        click(),
    )(ctx.action_ctx())


def open_store(ctx) -> Result:
    return do(move().image(f"{_DIR}/gong-hui-store.png"), click())(ctx.action_ctx())


def wen_ding_ling(ctx) -> Result:
    return do(move().image(f"{_DIR}/wen_ding_ling.png"), click())(ctx.action_ctx())


def tian_ming_ling(ctx) -> Result:
    return do(move().image(f"{_DIR}/tian_ming_ling.png"), click())(ctx.action_ctx())


def tian_fa_ling(ctx) -> Result:
    return do(move().image(f"{_DIR}/tian_fa_ling.png"), click())(ctx.action_ctx())


def jun_ling_zhuang(ctx) -> Result:
    return do(move().image(f"{_DIR}/jun_ling_zhuang.png"), click())(ctx.action_ctx())


def finish(ctx) -> Result:
    step_go_back(ctx)
    return Result.success()
