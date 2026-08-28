"""选将 mod 与画面重定位。"""

from __future__ import annotations

import time

from vision_bot.actions import click, do, move
from vision_bot.apps.ming_jiang_sha.paths import DATA_ROOT
from vision_bot.core.input import input_text as type_text
from vision_bot.perception.signal import Signal
from vision_bot.perception.snapshot import ScreenSnapshot, capture
from vision_bot.runtime.context import RunContext
from vision_bot.runtime.result import Result

SIGNALS: dict[str, Signal] = {
    "enter.select_wu_jiang": Signal(
        template=f"{DATA_ROOT}/qian_li_dan_qi/enter_battle/select_wu_jiang.png"
    ),
    "enter.search": Signal(
        template=f"{DATA_ROOT}/qian_li_dan_qi/enter_battle/search.png"
    ),
}

DETECT: set[str] = set(SIGNALS)


def detect(snap: ScreenSnapshot, ctx: RunContext | None = None) -> str | None:
    if snap.found("enter.select_wu_jiang"):
        return "qldq.battle_select.enter_pick.select_wu_jiang"
    return None


def relocate(ctx: RunContext) -> str | None:
    snap = capture(ctx.registry, ctx.base_dir, DETECT)
    return detect(snap, ctx)


def select_wu_jiang(ctx) -> Result:
    do(
        move().image(f"{DATA_ROOT}/qian_li_dan_qi/enter_battle/select_wu_jiang.png"),
        click(),
    )()
    ctx.goto("qldq.battle_select.enter_pick.focus_search")
    return Result.success()


def focus_search(ctx) -> Result:
    r = do(
        move().image(f"{DATA_ROOT}/qian_li_dan_qi/enter_battle/search.png"),
        move().by(-160, 0),
        click().pause(0.3),
    )()
    if not r.ok:
        return Result.fail("聚焦搜索框失败")
    ctx.goto("qldq.battle_select.enter_pick.type_name")
    return Result.success()


def type_name(ctx) -> Result:
    name = str(ctx.params.get("wu_jiang", "吕布")).strip()
    if not name:
        return Result.fail("武将名为空")
    type_text(name, method="paste")
    time.sleep(0.2)
    ctx.goto("qldq.battle_select.enter_pick.click_search")
    return Result.success()


def click_search(ctx) -> Result:
    do(
        move().image(f"{DATA_ROOT}/qian_li_dan_qi/enter_battle/search.png"),
        click(),
    )()
    ctx.goto("qldq.battle_select.enter_pick.click_general")
    return Result.success()


def click_general(ctx) -> Result:
    do(
        move().image(f"{DATA_ROOT}/qian_li_dan_qi/enter_battle/lv_bu.png"),
        click(),
    )()
    ctx.goto("qldq.battle_select.enter_ready.try_start")
    return Result.success()
