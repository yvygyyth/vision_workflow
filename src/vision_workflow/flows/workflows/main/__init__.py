"""复杂流程：邮箱一键领取。"""

from vision_workflow.flows.parts.dang_qing_ge import FLOW as dang_qing_ge
from vision_workflow.flows.parts.handle_fail import FLOW as handle_fail
from vision_workflow.flows.parts.mail import FLOW as mail
from vision_workflow.flows.parts.wrap_up import FLOW as wrap_up
from vision_workflow.module import Workflow

WORKFLOW = Workflow(
    id="main",
    name="邮箱一键领取",
    flows=[mail, dang_qing_ge, wrap_up, handle_fail],
    entry="mail",
)
