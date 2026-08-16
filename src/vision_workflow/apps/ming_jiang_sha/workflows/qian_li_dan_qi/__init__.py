"""复杂流程：千里单骑。"""

from vision_workflow.apps.ming_jiang_sha.parts.qian_li_dan_qi import FLOW as qian_li_dan_qi
from vision_workflow.module import FlowNode, Workflow

WORKFLOW = Workflow(
    id="qian_li_dan_qi",
    name="千里单骑",
    description="选择武将并搜索输入武将名",
    entry="qian_li_dan_qi",
    nodes=[
        FlowNode(qian_li_dan_qi, params={"wu_jiang": "吕布"}),
    ],
)
