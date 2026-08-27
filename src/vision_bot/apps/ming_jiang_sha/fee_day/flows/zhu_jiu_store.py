"""煮酒店铺。"""

from __future__ import annotations

from vision_bot.actions import click, do, move
from vision_bot.apps.ming_jiang_sha.actions import step_go_back
from vision_bot.apps.ming_jiang_sha.paths import FEE_DAY
from vision_bot.runtime.result import Result

_DIR = f"{FEE_DAY}/zhu_jiu_store"


def entry(ctx) -> Result:
    return do(move().image(f"{_DIR}/entry.png"), click())(ctx.action_ctx())


def qing_mei_store(ctx) -> Result:
    return do(move().image(f"{_DIR}/qing_mei-store.png"), click())(ctx.action_ctx())


def finish(ctx) -> Result:
    step_go_back(ctx)
    return Result.success()
