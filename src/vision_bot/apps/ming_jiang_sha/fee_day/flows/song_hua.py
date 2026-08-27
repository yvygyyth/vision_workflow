from __future__ import annotations

from vision_bot.actions import click, do, move
from vision_bot.apps.ming_jiang_sha.flow_helpers import scroll_center
from vision_bot.apps.ming_jiang_sha.paths import FEE_DAY
from vision_bot.runtime.result import Result
from vision_bot.apps.ming_jiang_sha.actions import go_back

_DIR = f"{FEE_DAY}/song_hua"

def open_entry(ctx) -> Result:
    return do(move().image(f"{_DIR}/hao_you.png"), click())()

def open_song_li(ctx) -> Result:
    return do(move().image(f"{_DIR}/song_li.png"), click())()

def open_x100(ctx) -> Result:
    return do(move().image(f"{_DIR}/100.png"), click())()

def open_you_cai_hua(ctx) -> Result:
    return do(move().image(f"{_DIR}/you_cai_hua.png"), click())()

def zeng_song(ctx) -> Result:
    do(move().to(470, 420).raw(), click())()
    return Result.success()

def finish(ctx) -> Result:
    ctx.sleep(2.0)
    go_back()
    return Result.success()

def finish_2(ctx) -> Result:
    go_back()
    return Result.success()

