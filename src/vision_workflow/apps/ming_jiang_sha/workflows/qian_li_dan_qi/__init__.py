"""复杂流程：千里单骑。"""

from vision_workflow.apps.ming_jiang_sha.parts.qian_li_dan_qi.battle import FLOW as battle
from vision_workflow.apps.ming_jiang_sha.parts.qian_li_dan_qi.enter_battle import (
    FLOW as enter_battle,
)
from vision_workflow.module import FlowNode, Workflow

WORKFLOW = Workflow(
    id="qian_li_dan_qi",
    name="千里单骑",
    description="千里单骑",
    entry="enter_battle",
    nodes=[
        FlowNode(enter_battle, params={"wu_jiang": "吕布"}),
        FlowNode(battle),
    ],
)
