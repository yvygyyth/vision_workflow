"""进战 Flow。"""

from __future__ import annotations

import logging
import time

from vision_bot.actions import click, do, move
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.detect import relocate_enter
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.signals import ENTER_DETECT, snap_center, snap_found
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.state import bind_battle_state
from vision_bot.core.input import Mouse, input_text as type_text, press_key
from vision_bot.runtime.flow import Flow, StepResult
from vision_bot.runtime.types import BACK_TO_HUB, END, FAIL

logger = logging.getLogger(__name__)


def _check_done(ctx) -> StepResult:
    bind_battle_state(ctx)
    snap = ctx.snap(ENTER_DETECT)
    if snap_found(snap, "enter.battle_interface"):
        return StepResult.end(BACK_TO_HUB)
    return StepResult.ok(next_id="try_start")


def _try_start(ctx) -> StepResult:
    snap = ctx.snap({"enter.start"})
    c = snap_center(snap, "enter.start")
    if c is None:
        return StepResult.fail("无开始按钮")
    Mouse().move(*c).click().sleep(0.5).perform()
    return StepResult.ok(next_id="check_done")


def _recover(ctx) -> StepResult:
    for _ in range(3):
        press_key("esc")
        time.sleep(0.2)
    do(move().to(1980, 700).raw(), click())(ctx.action_ctx())
    time.sleep(0.2)
    do(move().to(1130, 700).raw(), click())(ctx.action_ctx())
    return StepResult.ok(next_id="try_start")


def _select_wu_jiang(ctx) -> StepResult:
    do(move().image("data/ming_jiang_sha/qian_li_dan_qi/enter_battle/select_wu_jiang.png"), click())(
        ctx.action_ctx()
    )
    return StepResult.ok(next_id="focus_search")


def _focus_search(ctx) -> StepResult:
    act = ctx.action_ctx()
    r = do(
        move().image("data/ming_jiang_sha/qian_li_dan_qi/enter_battle/search.png"),
        move().by(-160, 0),
        click().pause(0.3),
    )(act)
    if r.failed:
        return StepResult.fail("聚焦搜索框失败")
    return StepResult.ok(next_id="type_name")


def _type_name(ctx) -> StepResult:
    name = str(ctx.params.get("wu_jiang", "吕布")).strip()
    if not name:
        return StepResult.fail("武将名为空")
    type_text(name, method="paste")
    time.sleep(0.2)
    return StepResult.ok(next_id="click_search")


def _click_search(ctx) -> StepResult:
    do(move().image("data/ming_jiang_sha/qian_li_dan_qi/enter_battle/search.png"), click())(
        ctx.action_ctx()
    )
    return StepResult.ok(next_id="click_general")


def _click_general(ctx) -> StepResult:
    do(move().image("data/ming_jiang_sha/qian_li_dan_qi/enter_battle/lv_bu.png"), click())(
        ctx.action_ctx()
    )
    return StepResult.ok(next_id="try_start")


def build() -> Flow:
    return Flow(
        id="enter_battle",
        name="进入战斗",
        entry="check_done",
        relocate=relocate_enter,
        steps={
            "check_done": _check_done,
            "try_start": _try_start,
            "recover": _recover,
            "select_wu_jiang": _select_wu_jiang,
            "focus_search": _focus_search,
            "type_name": _type_name,
            "click_search": _click_search,
            "click_general": _click_general,
        },
        routes={"try_start": {FAIL: "recover"}},
        on={BACK_TO_HUB: END},
    )
