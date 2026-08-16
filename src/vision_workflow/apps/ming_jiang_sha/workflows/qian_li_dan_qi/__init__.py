"""复杂流程：千里单骑。"""

from vision_workflow.apps.ming_jiang_sha.parts.qian_li_dan_qi.battle_select import (
    FLOW as battle_select,
)
from vision_workflow.apps.ming_jiang_sha.parts.qian_li_dan_qi.battle_select.state import (
    bind_battle_state,
    clear_battle_state,
)
from vision_workflow.apps.ming_jiang_sha.parts.qian_li_dan_qi.enter_battle import (
    FLOW as enter_battle,
)
from vision_workflow.apps.ming_jiang_sha.parts.qian_li_dan_qi.fight import FLOW as fight
from vision_workflow.module import FlowNode, FlowRouter, Workflow, WorkflowLifecycle
from vision_workflow.status import FlowStatus

WORKFLOW = Workflow(
    id="qian_li_dan_qi",
    name="千里单骑",
    description="千里单骑",
    entry="enter_battle",
    lifecycle=WorkflowLifecycle(
        on_enter=bind_battle_state,
        on_exit=clear_battle_state,
    ),
    nodes=[
        FlowNode(enter_battle, params={"wu_jiang": "吕布"}),
        FlowNode(
            battle_select,
            router=FlowRouter(
                on={
                    FlowStatus.FULFILLED: "fight",
                    FlowStatus.REJECTED: None,
                }
            ),
        ),
        FlowNode(
            fight,
            router=FlowRouter(
                on={
                    FlowStatus.FULFILLED: "battle_select",
                    FlowStatus.REJECTED: None,
                }
            ),
        ),
    ],
)
