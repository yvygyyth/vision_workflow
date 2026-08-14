"""内置复杂流程目录。

Flow / Module 仅供脚本编排（见 ``parts/``）；
面向用户的可执行单位是 Workflow（见 ``workflows/``）。

- 正式组合：``workflows/<id>/`` 导出 ``WORKFLOW``
- 单流程调试：``workflows/solo/__init__.py``（每个 Workflow 只包一个 Flow）

再加入下方 ``WORKFLOWS``。
"""

from vision_workflow.flows.workflows.main import WORKFLOW as main_workflow
from vision_workflow.flows.workflows.solo import WORKFLOWS as solo_workflows
from vision_workflow.module import Workflow

WORKFLOW = main_workflow  # CLI / 默认入口兼容

WORKFLOWS: list[Workflow] = [main_workflow, *solo_workflows]


def get_workflow(workflow_id: str) -> Workflow:
    for wf in WORKFLOWS:
        if wf.id == workflow_id:
            return wf
    raise KeyError(f"未知复杂流程: {workflow_id}，可选: {[w.id for w in WORKFLOWS]}")


def workflow_choices() -> list[tuple[str, str]]:
    """UI 用：(display_name, workflow_id)。"""
    return [(w.display_name, w.id) for w in WORKFLOWS]
