"""子流程：千里单骑 · 诸葛亮事件。"""

from vision_workflow.apps.ming_jiang_sha.parts.qian_li_dan_qi.zhu_ge_liang.actions import (
    finish_placeholder,
)
from vision_workflow.module import Flow, Module, abort
from vision_workflow.status import FULFILLED, REJECTED

FLOW = Flow(
    id="zhu_ge_liang",
    name="诸葛亮事件",
    description="事件逻辑待补；结束后回三选一",
    entry="finish",
    modules=[
        Module(
            id="finish",
            name="占位结束",
            description="事件细节待补",
            event=finish_placeholder,
            on={
                FULFILLED: lambda m: m.end(),
                REJECTED: abort,
            },
        ),
    ],
)
