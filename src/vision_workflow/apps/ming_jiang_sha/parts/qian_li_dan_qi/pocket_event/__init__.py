"""子流程：千里单骑锦囊事件（袋子）。"""

from vision_workflow.apps.ming_jiang_sha.parts.qian_li_dan_qi.pocket_event.actions import (
    ENTER_BATTLE,
    check_cancel_ready,
    pick_event_pattern,
)
from vision_workflow.module import Flow, Module, abort, to
from vision_workflow.status import FULFILLED, REJECTED

FLOW = Flow(
    id="pocket_event",
    name="锦囊事件",
    description="随机点花纹 → 看取消；有则进战斗，无则继续，花纹没了回三选一",
    entry="pick_event_pattern",
    modules=[
        Module(
            id="pick_event_pattern",
            name="随机点花纹",
            description="在找到的 event_pattern 中随机点一个；没有则结束",
            event=pick_event_pattern,
            on={
                "clicked": to("check_cancel"),
                FULFILLED: lambda m: m.end(),
                REJECTED: abort,
            },
        ),
        Module(
            id="check_cancel",
            name="确认取消出现",
            description="识到 cancel 则进 in_battle；否则继续点花纹",
            event=check_cancel_ready,
            on={
                ENTER_BATTLE: lambda m: m.end(),
                "continue": to("pick_event_pattern"),
                REJECTED: abort,
            },
        ),
    ],
)
