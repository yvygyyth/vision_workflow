"""子流程：千里单骑巴清商店。"""

from vision_workflow.apps.ming_jiang_sha.common.actions import confirm, go_back
from vision_workflow.apps.ming_jiang_sha.parts.qian_li_dan_qi.ba_qing_store.actions import (
    choose_token,
    click_confirm,
    click_go_back,
    click_token_slot,
)
from vision_workflow.module import Flow, Module, ModuleConfig, abort, onward, to
from vision_workflow.status import FULFILLED, REJECTED

_CLICK = {FULFILLED: onward, REJECTED: abort}
_EXIT = {FULFILLED: to("click_go_back"), REJECTED: to("click_go_back")}

FLOW = Flow(
    id="ba_qing_store",
    name="巴清商店",
    description="可选买格子 → 按优先表买信物 → 返回退出；铜币不够则 Esc 后退出",
    entry="click_token_slot",
    modules=[
        Module(
            id="click_token_slot",
            name="购买信物背包格子",
            description="可选；识不到则跳过，直接买信物",
            event=click_token_slot,
            on={
                FULFILLED: to("slot_confirm"),
                REJECTED: to("choose_token"),
            },
        ),
        Module(
            id="slot_confirm",
            name="确认买格子",
            description="通用确认；没有确认框视为铜币不够",
            event=confirm,
            on={
                FULFILLED: to("choose_token"),
                REJECTED: to("esc_go_back"),
            }
        ),
        Module(
            id="choose_token",
            name="购买信物",
            description="OCR 三槽按 TOKEN_PRIORITY 点选；没有想要的则直接退出",
            event=choose_token,
            on={
                FULFILLED: to("token_confirm"),
                "skip": to("click_go_back"),
                REJECTED: to("click_go_back"),
            }
        ),
        Module(
            id="token_confirm",
            name="确认买信物",
            description="通用确认；识别不到视为铜币不够",
            event=confirm,
            on={
                FULFILLED: to("click_go_back"),
                REJECTED: to("esc_go_back"),
            }
        ),
        Module(
            id="esc_go_back",
            name="Esc返回",
            description="通用 go_back（Esc），关掉买不起的弹窗",
            event=go_back(),
            on=_EXIT,
        ),
        Module(
            id="click_go_back",
            name="返回",
            description="识别并点击本页 go_back",
            event=click_go_back,
            on=_CLICK,
        ),
        Module(
            id="click_confirm",
            name="确认退出",
            description="识别并点击商店内 confirm",
            event=click_confirm,
            on={
                FULFILLED: lambda m: m.end(),
                REJECTED: abort,
            },
        ),
    ],
)
