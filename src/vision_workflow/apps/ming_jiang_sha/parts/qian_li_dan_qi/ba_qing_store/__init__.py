"""子流程：千里单骑巴清商店。"""

from vision_workflow.apps.ming_jiang_sha.common.actions import confirm, go_back
from vision_workflow.apps.ming_jiang_sha.parts.qian_li_dan_qi.ba_qing_store.actions import (
    choose_token,
    click_confirm,
    click_go_back,
    click_token_slot,
    detect_no_buy,
    ensure_left,
)
from vision_workflow.module import Flow, Module, ModuleConfig, abort, onward, to
from vision_workflow.status import FULFILLED, REJECTED

_CLICK = {FULFILLED: onward, REJECTED: abort}
_EXIT = {FULFILLED: to("click_go_back"), REJECTED: to("click_go_back")}

FLOW = Flow(
    id="ba_qing_store",
    name="巴清商店",
    description="可选买格子 → 按优先表买信物 → 返回+确认 → 核验离店后再回三选一",
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
            description="通用确认；没有则看是否钱不够",
            event=confirm,
            on={
                FULFILLED: to("choose_token"),
                REJECTED: to("slot_no_buy"),
            },
        ),
        Module(
            id="slot_no_buy",
            name="格子钱不够判定",
            description="识到 no_buy 才 Esc 关弹窗；否则继续买信物",
            event=detect_no_buy,
            on={
                "no_buy": to("esc_go_back"),
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
            description="通用确认；没有则看是否钱不够",
            event=confirm,
            on={
                FULFILLED: to("click_go_back"),
                REJECTED: to("token_no_buy"),
            },
        ),
        Module(
            id="token_no_buy",
            name="信物钱不够判定",
            description="识到 no_buy 才 Esc 关弹窗；否则直接返回离店",
            event=detect_no_buy,
            on={
                "no_buy": to("esc_go_back"),
                FULFILLED: to("click_go_back"),
                REJECTED: to("click_go_back"),
            },
        ),
        Module(
            id="esc_go_back",
            name="Esc关弹窗",
            description="仅钱不够（no_buy）时 Esc 关弹窗，再返回离店",
            event=go_back(),
            on=_EXIT,
        ),
        Module(
            id="click_go_back",
            name="返回",
            description="点本页 go_back，弹出退出确认",
            event=click_go_back,
            on=_CLICK,
            config=ModuleConfig(delay_ms=600),
        ),
        Module(
            id="click_confirm",
            name="确认退出",
            description="点商店内 confirm；点完不论成败都去核验是否离店",
            event=click_confirm,
            on={
                FULFILLED: to("ensure_left"),
                REJECTED: to("ensure_left"),
            },
        ),
        Module(
            id="ensure_left",
            name="确认已离店",
            description="go_back 消失才结束回三选一；仍在则再点返回",
            event=ensure_left,
            on={
                FULFILLED: lambda m: m.end(),
                "still_here": to("click_go_back"),
                REJECTED: abort,
            },
        ),
    ],
)
