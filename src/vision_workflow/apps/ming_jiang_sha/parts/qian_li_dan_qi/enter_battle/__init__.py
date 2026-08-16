"""子流程：确保进入千里单骑战斗界面。"""

from vision_workflow.apps.ming_jiang_sha.common.actions import go_back
from vision_workflow.apps.ming_jiang_sha.parts.qian_li_dan_qi.enter_battle.actions import (
    check_battle_interface,
    click_lv_bu,
    click_search,
    click_select_wu_jiang,
    focus_search_input,
    try_click_start,
    type_wu_jiang,
)
from vision_workflow.module import Flow, Module, abort, onward, to
from vision_workflow.status import FULFILLED, REJECTED

_CLICK = {FULFILLED: onward, REJECTED: abort}
_OK = {FULFILLED: onward}

FLOW = Flow(
    id="enter_battle",
    name="进入战斗",
    description="确保进入千里单骑战斗界面",
    entry="check_battle",
    params={"wu_jiang": "吕布"},
    modules=[
        Module(
            id="check_battle",
            name="战斗界面",
            description="已在战斗则本 Flow 结束，否则去准备",
            event=check_battle_interface,
            on={
                FULFILLED: lambda m: m.end(),
                "need_prepare": to("try_start"),
                REJECTED: abort,
            },
        ),
        Module(
            id="try_start",
            name="开始",
            description="可开战则点开始，否则转选将；点完后回到 check_battle 复核",
            event=try_click_start,
            on={
                FULFILLED: to("check_battle"),
                "need_select": to("select_wu_jiang"),
                REJECTED: abort,
            },
        ),
        Module(
            id="select_wu_jiang",
            name="选择武将",
            description="点击选择武将入口",
            event=click_select_wu_jiang,
            on=_CLICK,
        ),
        Module(
            id="focus_search_input",
            name="聚焦搜索输入框",
            description="识图「搜索」后向左偏移点击输入框",
            event=focus_search_input,
            on=_CLICK,
        ),
        Module(
            id="type_wu_jiang",
            name="输入武将名",
            description="输入入参 wu_jiang",
            event=type_wu_jiang,
            on=_OK,
        ),
        Module(
            id="click_search",
            name="点击搜索",
            description="点击「搜索」按钮提交",
            event=click_search,
            on=_CLICK,
        ),
        Module(
            id="click_lv_bu",
            name="选择吕布",
            description="点击吕布头像",
            event=click_lv_bu,
            on=_CLICK,
        ),
        Module(
            id="go_back",
            name="返回",
            description="Esc 返回后再次尝试开始",
            event=go_back(),
            on={FULFILLED: to("try_start")},
        ),
    ],
)
