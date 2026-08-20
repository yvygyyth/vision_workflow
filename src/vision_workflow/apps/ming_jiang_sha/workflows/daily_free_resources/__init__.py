"""复杂流程：名将杀免费资源每日领取。"""

from vision_workflow.apps.ming_jiang_sha.parts.actaivity import FLOW as activity
from vision_workflow.apps.ming_jiang_sha.parts.ba_qing_store import FLOW as ba_qing_store
from vision_workflow.apps.ming_jiang_sha.parts.dang_qing_ge import FLOW as dang_qing_ge
from vision_workflow.apps.ming_jiang_sha.parts.gong_hui import FLOW as gong_hui
from vision_workflow.apps.ming_jiang_sha.parts.mail import FLOW as mail
from vision_workflow.apps.ming_jiang_sha.parts.zhan_yi_store import FLOW as zhan_yi_store
from vision_workflow.apps.ming_jiang_sha.parts.zhu_jiu_store import FLOW as zhu_jiu_store
from vision_workflow.module import FlowNode, Workflow

WORKFLOW = Workflow(
    id="daily_free_resources",
    name="名将杀免费资源每日领取",
    description="依次领取邮件、丹青阁、煮酒店铺、战役商店、巴清商店、活动、公会店铺资源",
    entry="mail",
    nodes=[
        FlowNode(mail),
        FlowNode(dang_qing_ge),
        FlowNode(zhu_jiu_store),
        FlowNode(zhan_yi_store),
        FlowNode(ba_qing_store),
        FlowNode(activity),
        FlowNode(gong_hui),
    ],
)
