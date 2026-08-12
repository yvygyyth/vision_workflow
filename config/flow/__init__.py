"""工作流入口：聚合各子流程文件夹。

目录约定（一个子流程一个文件夹）::

    config/flow/
      __init__.py              # WORKFLOW
      mail/
        __init__.py            # FLOW
        actions.py             # 本流程专属事件（强相关就放旁边）
      wrap_up/
      handle_fail/
"""

from config.flow.handle_fail import FLOW as handle_fail_flow
from config.flow.mail import FLOW as mail_flow
from config.flow.wrap_up import FLOW as wrap_up_flow
from vision_workflow.module import Workflow

FLOWS = [mail_flow, wrap_up_flow, handle_fail_flow]
ENTRY = "mail"

WORKFLOW = Workflow(
    id="main",
    name="邮箱一键领取",
    flows=FLOWS,
    entry=ENTRY,
    module_delay_ms=100,  # 模块执行后 → 下一模块
    flow_delay_ms=200,  # 流程执行后 → 下一流程
)
