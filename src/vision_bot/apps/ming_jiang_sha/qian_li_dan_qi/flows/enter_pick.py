"""选将 mod 与画面重定位。"""

from __future__ import annotations

import time

from vision_bot.actions import click, do, move
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.ids import qmod
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.signals import ENTER_DETECT, snap_found
from vision_bot.core.input import input_text as type_text
from vision_bot.perception.snapshot import ScreenSnapshot, capture
from vision_bot.runtime.context import RunContext
from vision_bot.runtime.result import Result

_FLOW = "battle_select.enter_pick"
_READY = "battle_select.enter_ready"


def detect(snap: ScreenSnapshot, ctx: RunContext | None = None) -> str | None:
    if snap_found(snap, "enter.select_wu_jiang"):
        return qmod(_FLOW, "select_wu_jiang")
    return None


def relocate(ctx: RunContext) -> str | None:
    snap = capture(ctx.registry, ctx.base_dir, ENTER_DETECT)
    return detect(snap, ctx)


def select_wu_jiang(ctx) -> Result:
    do(move().image("data/ming_jiang_sha/qian_li_dan_qi/enter_battle/select_wu_jiang.png"), click())(
        ctx.action_ctx()
    )
    ctx.goto(qmod(_FLOW, "focus_search"))
    return Result.success()


def focus_search(ctx) -> Result:
    act = ctx.action_ctx()
    r = do(
        move().image("data/ming_jiang_sha/qian_li_dan_qi/enter_battle/search.png"),
        move().by(-160, 0),
        click().pause(0.3),
    )(act)
    if not r.ok:
        return Result.fail("聚焦搜索框失败")
    ctx.goto(qmod(_FLOW, "type_name"))
    return Result.success()


def type_name(ctx) -> Result:
    name = str(ctx.params.get("wu_jiang", "吕布")).strip()
    if not name:
        return Result.fail("武将名为空")
    type_text(name, method="paste")
    time.sleep(0.2)
    ctx.goto(qmod(_FLOW, "click_search"))
    return Result.success()


def click_search(ctx) -> Result:
    do(move().image("data/ming_jiang_sha/qian_li_dan_qi/enter_battle/search.png"), click())(
        ctx.action_ctx()
    )
    ctx.goto(qmod(_FLOW, "click_general"))
    return Result.success()


def click_general(ctx) -> Result:
    do(move().image("data/ming_jiang_sha/qian_li_dan_qi/enter_battle/lv_bu.png"), click())(
        ctx.action_ctx()
    )
    ctx.goto(qmod(_READY, "try_start"))
    return Result.success()
