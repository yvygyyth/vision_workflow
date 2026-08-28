"""煮酒店铺。"""

from __future__ import annotations

from vision_bot.actions import click, do, move
from vision_bot.apps.ming_jiang_sha.actions import go_back
from vision_bot.apps.ming_jiang_sha.paths import FEE_DAY
from vision_bot.runtime.result import Result


def entry(ctx) -> Result:
    return do(move().image(f"{FEE_DAY}/zhu_jiu_store/entry.png"), click())()


def qing_mei_store(ctx) -> Result:
    return do(move().image(f"{FEE_DAY}/zhu_jiu_store/qing_mei-store.png"), click())()


def finish(ctx) -> Result:
    go_back()
    return Result.success()
