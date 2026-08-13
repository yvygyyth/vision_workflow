"""复杂流程：仅执行战役商店。"""

from vision_workflow.flows.parts.zhan_yi_store import FLOW as zhan_yi_store
from vision_workflow.module import FlowNode, Workflow

WORKFLOW = Workflow(
    id="zhan_yi_store",
    name="战役商店",
    entry="zhan_yi_store",
    nodes=[FlowNode(zhan_yi_store)],
)
