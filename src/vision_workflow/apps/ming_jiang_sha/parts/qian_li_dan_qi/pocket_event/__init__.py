"""子流程：千里单骑锦囊事件（袋子）。"""

from vision_workflow.apps.ming_jiang_sha.parts.qian_li_dan_qi.pocket_event.actions import (
    pick_event_pattern,
)
from vision_workflow.module import Flow, Module, abort
from vision_workflow.status import FULFILLED, REJECTED

FLOW = Flow(
    id="pocket_event",
    name="锦囊事件",
    description="随机点选事件花纹，直到画面上不再出现",
    entry="pick_event_pattern",
    modules=[
        Module(
            id="pick_event_pattern",
            name="随机点花纹",
            description="在找到的 event_pattern 中随机点一个；没有则结束",
            event=pick_event_pattern,
            on={
                "again": lambda m: m.again(),
                FULFILLED: lambda m: m.end(),
                REJECTED: abort,
            },
        ),
    ],
)
