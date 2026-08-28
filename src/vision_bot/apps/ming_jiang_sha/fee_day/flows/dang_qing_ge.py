"""丹青阁。"""

from __future__ import annotations

from vision_bot.actions import click, do, move
from vision_bot.apps.ming_jiang_sha.paths import FEE_DAY
from vision_bot.runtime.result import Result


def open_icon(ctx) -> Result:
    return do(move().image(f"{FEE_DAY}/dang_qing_ge/dang_qing_ge-icon.png"), click())()


def day_libao(ctx) -> Result:
    return do(move().image(f"{FEE_DAY}/dang_qing_ge/day-libao.png"), click())()
