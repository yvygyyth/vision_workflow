"""进战 Flow。"""

from __future__ import annotations

import logging
import time

from vision_bot.actions import click, do, move
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.detect import qmod, relocate_enter
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.signals import ENTER_DETECT, snap_center, snap_found
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.state import bind_battle_state
from vision_bot.core.input import Mouse, input_text as type_text, press_key
from vision_bot.runtime.builders import flow, mod
from vision_bot.runtime.flow import Flow
from vision_bot.runtime.result import Result

logger = logging.getLogger(__name__)


def _check_done(ctx) -> Result:
    bind_battle_state(ctx)
    snap = ctx.snap(ENTER_DETECT)
    if snap_found(snap, "enter.battle_interface"):
        return Result.success()
    return Result.fail("未进战")


def _try_start(ctx) -> Result:
    snap = ctx.snap({"enter.start"})
    c = snap_center(snap, "enter.start")
    if c is None:
        ctx.goto(qmod("enter_battle", "recover"))
        return Result.success()
    Mouse().move(*c).click().sleep(0.5).perform()
    ctx.goto(qmod("enter_battle", "check_done"))
    return Result.success()


def _recover(ctx) -> Result:
    for _ in range(3):
        press_key("esc")
        time.sleep(0.2)
    do(move().to(1980, 700).raw(), click())(ctx.action_ctx())
    time.sleep(0.2)
    do(move().to(1130, 700).raw(), click())(ctx.action_ctx())
    ctx.goto(qmod("enter_battle", "try_start"))
    return Result.success()


def _select_wu_jiang(ctx) -> Result:
    do(move().image("data/ming_jiang_sha/qian_li_dan_qi/enter_battle/select_wu_jiang.png"), click())(
        ctx.action_ctx()
    )
    ctx.goto(qmod("enter_battle", "focus_search"))
    return Result.success()


def _focus_search(ctx) -> Result:
    act = ctx.action_ctx()
    r = do(
        move().image("data/ming_jiang_sha/qian_li_dan_qi/enter_battle/search.png"),
        move().by(-160, 0),
        click().pause(0.3),
    )(act)
    if not r.ok:
        return Result.fail("聚焦搜索框失败")
    ctx.goto(qmod("enter_battle", "type_name"))
    return Result.success()


def _type_name(ctx) -> Result:
    name = str(ctx.params.get("wu_jiang", "吕布")).strip()
    if not name:
        return Result.fail("武将名为空")
    type_text(name, method="paste")
    time.sleep(0.2)
    ctx.goto(qmod("enter_battle", "click_search"))
    return Result.success()


def _click_search(ctx) -> Result:
    do(move().image("data/ming_jiang_sha/qian_li_dan_qi/enter_battle/search.png"), click())(
        ctx.action_ctx()
    )
    ctx.goto(qmod("enter_battle", "click_general"))
    return Result.success()


def _click_general(ctx) -> Result:
    do(move().image("data/ming_jiang_sha/qian_li_dan_qi/enter_battle/lv_bu.png"), click())(
        ctx.action_ctx()
    )
    ctx.goto(qmod("enter_battle", "try_start"))
    return Result.success()


def build() -> Flow:
    return flow(
        "qldq.enter_battle",
        "进入战斗",
        children=[
            mod("qldq.enter_battle.check_done", "检查进战", _check_done),
            mod("qldq.enter_battle.try_start", "点击开始", _try_start),
            mod("qldq.enter_battle.recover", "恢复", _recover),
            mod("qldq.enter_battle.select_wu_jiang", "选武将", _select_wu_jiang),
            mod("qldq.enter_battle.focus_search", "聚焦搜索", _focus_search),
            mod("qldq.enter_battle.type_name", "输入武将", _type_name),
            mod("qldq.enter_battle.click_search", "搜索", _click_search),
            mod("qldq.enter_battle.click_general", "选吕布", _click_general),
        ],
        relocate=[relocate_enter],
    )
