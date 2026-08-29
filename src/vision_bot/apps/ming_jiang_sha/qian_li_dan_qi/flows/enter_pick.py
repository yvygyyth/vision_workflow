"""选将 mod 与画面重定位。"""

from __future__ import annotations

import time

from vision_bot.actions import click, do, move
from vision_bot.apps.ming_jiang_sha.paths import QLDQ
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.state import bind_battle_state
from vision_bot.core.input import Mouse, input_text as type_text
from vision_bot.runtime.context import RunContext
from vision_bot.runtime.relocate import RelocateRule
from vision_bot.runtime.result import Result
from vision_bot.vision import snap

START = f"{QLDQ}/enter_battle/start.png"
UN_START = f"{QLDQ}/enter_battle/un_start.png"
SELECT_WU_JIANG = f"{QLDQ}/enter_battle/select_wu_jiang.png"

DETECT: set[str] = {START, UN_START, SELECT_WU_JIANG}

CLICK_START = "qldq.battle_select.enter_pick.click_start"


def _has_start(ctx: RunContext) -> bool:
    return snap(DETECT).found(START)


def _un_start_without_select(ctx: RunContext) -> bool:
    s = snap(DETECT)
    return s.found(UN_START) and not s.found(SELECT_WU_JIANG)


def _has_select_wu_jiang(ctx: RunContext) -> bool:
    return snap(DETECT).found(SELECT_WU_JIANG)


relocate: list[RelocateRule] = [
    RelocateRule(when=_has_start, then=CLICK_START),
    RelocateRule(when=_un_start_without_select, then=None),
    RelocateRule(
        when=_has_select_wu_jiang,
        then="qldq.battle_select.enter_pick.focus_search",
    ),
]


def select_wu_jiang(ctx) -> Result:
    shot = snap(UN_START, SELECT_WU_JIANG)
    if not shot.all:
        if not shot.found(UN_START):
            return Result.fail("无 un_start")
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
    if snap(SELECT_WU_JIANG).ok:
        return Result.fail("仍在选将界面")
    return Result.success()


def click_start(ctx) -> Result:
    r = snap(START)
    if not r.ok or not r.value or not r.value.center:
        return Result.fail("无 start")
    Mouse().move(*r.value.center).click().sleep(0.5).perform()
    bind_battle_state(ctx)
    return Result.success()
