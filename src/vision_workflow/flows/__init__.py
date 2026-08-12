"""内置工作流：子流程各占一个子包。

目录约定::

    vision_workflow/flows/
      __init__.py              # WORKFLOW
      mail/
        __init__.py            # FLOW
        actions.py
      wrap_up/
      handle_fail/
"""

from vision_workflow.flows.dang_qing_ge import FLOW as dang_qing_ge_flow
from vision_workflow.flows.handle_fail import FLOW as handle_fail_flow
from vision_workflow.flows.mail import FLOW as mail_flow
from vision_workflow.flows.wrap_up import FLOW as wrap_up_flow
from vision_workflow.module import Workflow

DEFAULT_FLOW_TARGET = "vision_workflow.flows"

FLOWS = [mail_flow, dang_qing_ge_flow, wrap_up_flow, handle_fail_flow]
ENTRY = "mail"

WORKFLOW = Workflow(
    id="main",
    name="邮箱一键领取",
    flows=FLOWS,
    entry=ENTRY,
    module_delay_ms=100,  # 模块执行后 → 下一模块
    flow_delay_ms=200,  # 流程执行后 → 下一流程
)
