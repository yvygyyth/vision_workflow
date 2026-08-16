"""子流程：千里单骑战斗（选关后的开打 / 结算）。"""

from vision_workflow.module import Flow, Module, onward
from vision_workflow.status import FULFILLED


def _placeholder(m):
    m.log("fight flow placeholder")
    return FULFILLED


FLOW = Flow(
    id="fight",
    name="开打",
    description="千里单骑战斗过程（逻辑待补）",
    entry="ready",
    modules=[
        Module(
            id="ready",
            name="战斗中",
            description="开打与结算（逻辑待补）",
            event=_placeholder,
            on={FULFILLED: onward},
        ),
    ],
)
