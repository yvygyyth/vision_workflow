"""单流程调试用复杂流程：全部堆在本文件，每个 Workflow 只包一个 Flow。"""

from vision_workflow.flows.parts.ba_qing_store import FLOW as ba_qing_store
from vision_workflow.flows.parts.dang_qing_ge import FLOW as dang_qing_ge
from vision_workflow.flows.parts.mail import FLOW as mail
from vision_workflow.flows.parts.zhan_yi_store import FLOW as zhan_yi_store
from vision_workflow.flows.parts.zhu_jiu_store import FLOW as zhu_jiu_store
from vision_workflow.module import Flow, FlowNode, Workflow


def _solo(flow: Flow) -> Workflow:
    return Workflow(
        id=flow.id,
        name=flow.display_name,
        description=flow.description or f"单独调试：{flow.display_name}",
        entry=flow.id,
        nodes=[FlowNode(flow)],
    )


WORKFLOWS: list[Workflow] = [
    _solo(mail),
    _solo(dang_qing_ge),
    _solo(zhu_jiu_store),
    _solo(zhan_yi_store),
    _solo(ba_qing_store),
]
