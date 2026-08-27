"""丹青阁。"""

from __future__ import annotations

from vision_bot.actions import click, do, move
from vision_bot.apps.ming_jiang_sha.paths import DATA_ROOT
from vision_bot.runtime.result import Result

_DIR = f"{DATA_ROOT}/dang_qing_ge"


def open_icon(ctx) -> Result:
    return do(move().image(f"{_DIR}/dang_qing_ge-icon.png"), click())(ctx.action_ctx())


def day_libao(ctx) -> Result:
    return do(move().image(f"{_DIR}/day-libao.png"), click())(ctx.action_ctx())
