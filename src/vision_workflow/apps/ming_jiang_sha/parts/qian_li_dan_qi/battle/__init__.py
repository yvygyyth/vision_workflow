"""子流程：千里单骑战斗界面。"""

from vision_workflow.module import Flow, Module, onward
from vision_workflow.status import FULFILLED


def _placeholder(m):
    """战斗逻辑待补充；先占位成功结束。"""
    m.log("battle flow placeholder")
    return FULFILLED


FLOW = Flow(
    id="battle",
    name="战斗",
    description="千里单骑战斗界面",
    entry="ready",
    modules=[
        Module(
            id="ready",
            name="进入战斗",
            description="已进入战斗界面（逻辑待补充）",
            event=_placeholder,
            on={FULFILLED: onward},
        ),
    ],
)
