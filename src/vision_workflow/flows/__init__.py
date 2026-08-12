"""内置复杂流程目录。

Flow / Module 仅供脚本编排；面向用户的可执行单位是 Workflow（复杂流程）。
"""

from vision_workflow.flows.dang_qing_ge import FLOW as dang_qing_ge_flow
from vision_workflow.flows.handle_fail import FLOW as handle_fail_flow
from vision_workflow.flows.mail import FLOW as mail_flow
from vision_workflow.flows.wrap_up import FLOW as wrap_up_flow
from vision_workflow.module import Workflow

WORKFLOW = Workflow(
    id="main",
    name="邮箱一键领取",
    flows=[mail_flow, dang_qing_ge_flow, wrap_up_flow, handle_fail_flow],
    entry="mail",
)

# 用户可选的复杂流程目录（未来可扩展多项 / 自定义）
WORKFLOWS: list[Workflow] = [WORKFLOW]


def get_workflow(workflow_id: str) -> Workflow:
    for wf in WORKFLOWS:
        if wf.id == workflow_id:
            return wf
    raise KeyError(f"未知复杂流程: {workflow_id}，可选: {[w.id for w in WORKFLOWS]}")


def workflow_choices() -> list[tuple[str, str]]:
    """UI 用：(display_name, workflow_id)。"""
    return [(w.display_name, w.id) for w in WORKFLOWS]
