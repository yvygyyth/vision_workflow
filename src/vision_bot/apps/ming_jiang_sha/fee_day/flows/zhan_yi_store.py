"""战役商店。"""

from __future__ import annotations

from vision_bot.actions import click, do, move
from vision_bot.apps.ming_jiang_sha.actions import go_back
from vision_bot.apps.ming_jiang_sha.flow_helpers import scroll_center
from vision_bot.apps.ming_jiang_sha.paths import FEE_DAY
from vision_bot.runtime.result import Result

_DIR = f"{FEE_DAY}/zhan_yi_store"


def open_entry(ctx) -> Result:
    return do(
        move().image(f"{_DIR}/entry.png", f"{_DIR}/entry2.png").match(timeout=5.0),
        click(),
    )()


def open_store(ctx) -> Result:
    return do(move().image(f"{_DIR}/zhan_yi-store.png"), click())()


def scroll(ctx) -> Result:
    return scroll_center(-120, times=10)


def finish(ctx) -> Result:
    go_back()
    return Result.success()
