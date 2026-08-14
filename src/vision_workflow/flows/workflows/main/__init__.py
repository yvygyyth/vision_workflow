"""复杂流程：名将杀免费资源每日领取。"""

from vision_workflow.flows.parts.dang_qing_ge import FLOW as dang_qing_ge
from vision_workflow.flows.parts.mail import FLOW as mail
from vision_workflow.flows.parts.zhan_yi_store import FLOW as zhan_yi_store
from vision_workflow.flows.parts.zhu_jiu_store import FLOW as zhu_jiu_store
from vision_workflow.module import FlowNode, Workflow

WORKFLOW = Workflow(
    id="main",
    name="名将杀免费资源每日领取",
    description="依次领取邮件、丹青阁、煮酒店铺、战役商店资源",
    entry="mail",
    nodes=[
        FlowNode(mail),
        FlowNode(dang_qing_ge),
        FlowNode(zhu_jiu_store),
        FlowNode(zhan_yi_store),
    ],
)
