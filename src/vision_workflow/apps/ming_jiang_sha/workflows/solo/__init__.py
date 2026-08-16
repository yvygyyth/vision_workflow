"""单流程调试用复杂流程：每个 Workflow 只包一个 Flow。"""

from vision_workflow.apps.ming_jiang_sha.parts.ba_qing_store import FLOW as ba_qing_store
from vision_workflow.apps.ming_jiang_sha.parts.dang_qing_ge import FLOW as dang_qing_ge
from vision_workflow.apps.ming_jiang_sha.parts.gong_hui import FLOW as gong_hui
from vision_workflow.apps.ming_jiang_sha.parts.mail import FLOW as mail
from vision_workflow.apps.ming_jiang_sha.parts.qian_li_dan_qi import FLOW as qian_li_dan_qi
from vision_workflow.apps.ming_jiang_sha.parts.zhan_yi_store import FLOW as zhan_yi_store
from vision_workflow.apps.ming_jiang_sha.parts.zhu_jiu_store import FLOW as zhu_jiu_store
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
    _solo(gong_hui),
    _solo(qian_li_dan_qi),
]
