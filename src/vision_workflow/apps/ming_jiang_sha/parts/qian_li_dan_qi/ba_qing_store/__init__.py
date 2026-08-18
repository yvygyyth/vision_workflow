"""子流程：千里单骑巴清商店。"""

from vision_workflow.apps.ming_jiang_sha.common.actions import confirm
from vision_workflow.apps.ming_jiang_sha.parts.qian_li_dan_qi.ba_qing_store.actions import (
    choose_token,
    click_confirm,
    click_go_back,
    click_token_slot,
    close_no_buy_popup,
    ensure_left,
)
from vision_workflow.module import Flow, Module, ModuleConfig, abort, onward, to
from vision_workflow.status import FULFILLED, REJECTED

_CLICK = {FULFILLED: onward, REJECTED: abort}

FLOW = Flow(
    id="ba_qing_store",
    name="巴清商店",
    description="可选买格子 → 按优先表买信物 → 返回+确认离店；Esc 仅在 no_buy 弹窗可见时按",
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
            description="通用确认；没有则去看钱不够弹窗",
            event=confirm,
            on={
                FULFILLED: to("choose_token"),
                REJECTED: to("slot_no_buy"),
            },
        ),
        Module(
            id="slot_no_buy",
            name="格子钱不够关窗",
            description="no_buy 还在才 Esc；关掉则跳过买信物，没有弹窗则继续买",
            event=close_no_buy_popup,
            on={
                "closed": to("click_go_back"),
                FULFILLED: to("choose_token"),
                REJECTED: to("choose_token"),
            },
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
            },
        ),
        Module(
            id="token_confirm",
            name="确认买信物",
            description="通用确认；没有则去看钱不够弹窗",
            event=confirm,
            on={
                FULFILLED: to("click_go_back"),
                REJECTED: to("token_no_buy"),
            },
        ),
        Module(
            id="token_no_buy",
            name="信物钱不够关窗",
            description="no_buy 还在才 Esc；没有弹窗绝不按，然后离店",
            event=close_no_buy_popup,
            on={
                "closed": to("click_go_back"),
                FULFILLED: to("click_go_back"),
                REJECTED: to("click_go_back"),
            },
        ),
        Module(
            id="click_go_back",
            name="返回",
            description="点本页 go_back，弹出退出确认；只点一次",
            event=click_go_back,
            on=_CLICK,
            config=ModuleConfig(delay_ms=600),
        ),
        Module(
            id="click_confirm",
            name="确认退出",
            description="点商店内 confirm；失败只重试确认，不再点返回",
            event=click_confirm,
            on={
                FULFILLED: to("ensure_left"),
                REJECTED: to("ensure_left"),
            },
            config=ModuleConfig(
                retry=3,
                retry_delay_ms=400,
                retry_on=[REJECTED],
            ),
        ),
        Module(
            id="ensure_left",
            name="确认已离店",
            description="go_back 消失才结束；仍在则只重试确认，不再点返回/Esc",
            event=ensure_left,
            on={
                FULFILLED: lambda m: m.end(),
                "still_here": to("click_confirm"),
                REJECTED: abort,
            },
        ),
    ],
)
