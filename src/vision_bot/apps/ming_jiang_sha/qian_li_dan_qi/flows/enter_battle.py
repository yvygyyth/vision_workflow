"""进战 mod：已选将 / 选将。"""

from __future__ import annotations

import time

from vision_bot.actions import click, do, move
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.detect import qmod
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.signals import ENTER_DETECT, snap_center, snap_found
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.state import bind_battle_state
from vision_bot.core.input import Mouse, input_text as type_text, press_key
from vision_bot.runtime.result import Result

_READY = "battle_select.enter_ready"
_PICK = "battle_select.enter_pick"


def check_done(ctx) -> Result:
    bind_battle_state(ctx)
    snap = ctx.snap(ENTER_DETECT)
    if snap_found(snap, "enter.battle_interface"):
        ctx.goto("qldq.battle_hub")
        return Result.success()
    return Result.fail("未进战")


def try_start(ctx) -> Result:
    snap = ctx.snap({"enter.start"})
    c = snap_center(snap, "enter.start")
    if c is None:
        ctx.goto(qmod(_READY, "recover"))
        return Result.success()
    Mouse().move(*c).click().sleep(0.5).perform()
    ctx.goto(qmod(_READY, "check_done"))
    return Result.success()


def recover(ctx) -> Result:
    for _ in range(3):
        press_key("esc")
        time.sleep(0.2)
    do(move().to(1980, 700).raw(), click())(ctx.action_ctx())
    time.sleep(0.2)
    do(move().to(1130, 700).raw(), click())(ctx.action_ctx())
    ctx.goto(qmod(_READY, "try_start"))
    return Result.success()


def select_wu_jiang(ctx) -> Result:
    do(move().image("data/ming_jiang_sha/qian_li_dan_qi/enter_battle/select_wu_jiang.png"), click())(
        ctx.action_ctx()
    )
    ctx.goto(qmod(_PICK, "focus_search"))
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
    ctx.goto(qmod(_PICK, "type_name"))
    return Result.success()


def type_name(ctx) -> Result:
    name = str(ctx.params.get("wu_jiang", "吕布")).strip()
    if not name:
        return Result.fail("武将名为空")
    type_text(name, method="paste")
    time.sleep(0.2)
    ctx.goto(qmod(_PICK, "click_search"))
    return Result.success()


def click_search(ctx) -> Result:
    do(move().image("data/ming_jiang_sha/qian_li_dan_qi/enter_battle/search.png"), click())(
        ctx.action_ctx()
    )
    ctx.goto(qmod(_PICK, "click_general"))
    return Result.success()


def click_general(ctx) -> Result:
    do(move().image("data/ming_jiang_sha/qian_li_dan_qi/enter_battle/lv_bu.png"), click())(
        ctx.action_ctx()
    )
    ctx.goto(qmod(_READY, "try_start"))
    return Result.success()
