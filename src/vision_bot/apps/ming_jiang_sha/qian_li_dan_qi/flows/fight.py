"""战斗 mod。"""

from __future__ import annotations

from vision_bot.actions import do, move
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.signals import snap_center
from vision_bot.core.input import Mouse
from vision_bot.events import click_match
from vision_bot.runtime.result import Result
from vision_bot.vision import find

_AUTO = "data/ming_jiang_sha/qian_li_dan_qi/fight/auto.png"
_CHALLENGE_END = "data/ming_jiang_sha/qian_li_dan_qi/fight/challenge_end.png"
_NEXT_STEP = "data/ming_jiang_sha/qian_li_dan_qi/fight/next_step.png"


def move_aside(ctx) -> Result:
    do(move().to(80, 80).raw())(ctx.action_ctx())
    return Result.success()


def click_cancel(ctx) -> Result:
    snap = ctx.snap({"fight.cancel"})
    c = snap_center(snap, "fight.cancel")
    if c:
        Mouse().move(*c).click().sleep(0.2).perform()
        return Result.success()
    return Result.fail("无 cancel")


def click_setting(ctx) -> Result:
    snap = ctx.snap({"fight.setting"})
    c = snap_center(snap, "fight.setting")
    if c:
        Mouse().move(*c).click().sleep(0.5).perform()
        return Result.success()
    return Result.fail("无 setting")


def click_auto(ctx) -> Result:
    result = find(_AUTO, timeout=1.0)
    if not result.ok:
        return Result.fail("无 auto")
    return click_match(result.value, pause=0.2)


def wait_end(ctx) -> Result:
    result = find(_CHALLENGE_END, timeout=1200, interval=5)
    if not result.ok:
        return Result.fail("挑战未结束")
    return click_match(result.value, pause=0.2)


def next_step(ctx) -> Result:
    for _ in range(5):
        result = find(_NEXT_STEP, timeout=1.2)
        if not result.ok or not result.value.center:
            break
        click_match(result.value, pause=0.4)
    return Result.success()
