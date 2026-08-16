"""子流程：千里单骑 · 十常侍事件。"""

from vision_workflow.apps.ming_jiang_sha.common.actions import confirm
from vision_workflow.apps.ming_jiang_sha.parts.qian_li_dan_qi.shi_chang_shi.actions import (
    check_cancel_ready,
    click_attack,
)
from vision_workflow.module import Flow, Module, ModuleConfig, abort, onward, to
from vision_workflow.status import FULFILLED, REJECTED

_CLICK = {FULFILLED: onward, REJECTED: abort}

FLOW = Flow(
    id="shi_chang_shi",
    name="十常侍事件",
    description="确认 → 连点 attack 直到取消出现 → in_battle",
    entry="confirm",
    modules=[
        Module(
            id="confirm",
            name="确认",
            description="公共确认框",
            event=confirm,
            on=_CLICK,
        ),
        Module(
            id="click_attack",
            name="连点攻击",
            description="识别 attack 后连续点击五下",
            event=click_attack,
            on={
                FULFILLED: to("check_cancel"),
                REJECTED: abort,
            },
            config=ModuleConfig(delay_ms=300),
        ),
        Module(
            id="check_cancel",
            name="确认取消出现",
            description="识到 cancel 才进战斗；否则继续点 attack",
            event=check_cancel_ready,
            on={
                FULFILLED: lambda m: m.end(),
                "need_attack": to("click_attack"),
                REJECTED: abort,
            },
        ),
    ],
)
