"""选将 mod 与画面重定位。"""

from __future__ import annotations

import time

from vision_bot.actions import click, do, move
from vision_bot.apps.ming_jiang_sha.paths import QLDQ
from vision_bot.core.input import input_text as type_text
from vision_bot.perception.snapshot import ScreenSnapshot, snap
from vision_bot.runtime.context import RunContext
from vision_bot.runtime.result import Result
from vision_bot.vision import find_once

SWITCH = f"{QLDQ}/enter_battle/switch.png"
SELECT_WU_JIANG = f"{QLDQ}/enter_battle/select_wu_jiang.png"

DETECT: set[str] = {SELECT_WU_JIANG}


def detect(shot: ScreenSnapshot, ctx: RunContext | None = None) -> str | None:
    if shot.found(SELECT_WU_JIANG):
        return "qldq.battle_select.enter_pick.select_wu_jiang"
    return None


def relocate(ctx: RunContext) -> str | None:
    shot = snap(DETECT)
    return detect(shot, ctx)


def select_wu_jiang(ctx) -> Result:
    shot = snap({SWITCH, SELECT_WU_JIANG})
    if not shot.found(SWITCH):
        return Result.fail("无 switch")
    if not shot.found(SELECT_WU_JIANG):
        return Result.fail("无 select_wu_jiang")
    do(
        move().image(SELECT_WU_JIANG),
        click(),
    )()
    return Result.success()


def focus_search(ctx) -> Result:
    r = do(
        move().image(f"{QLDQ}/enter_battle/search.png"),
        move().by(-160, 0),
        click().pause(0.3),
    )()
    if not r.ok:
        return Result.fail("聚焦搜索框失败")
    return Result.success()


def type_name(ctx) -> Result:
    name = str(ctx.params.get("wu_jiang", "吕布"))
    if not name:
        return Result.fail("武将名为空")
    type_text(name, method="paste")
    time.sleep(0.2)
    return Result.success()


def click_search(ctx) -> Result:
    do(
        move().image(f"{QLDQ}/enter_battle/search.png"),
        click(),
    )()
    return Result.success()


def click_general(ctx) -> Result:
    do(move().to(190, 1100).raw(), click())()
    if find_once(SELECT_WU_JIANG).ok:
        return Result.fail("仍在选将界面")
    return Result.success()
