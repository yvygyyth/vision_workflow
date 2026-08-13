"""内置复杂流程目录。

Flow / Module 仅供脚本编排（见 ``parts/``）；
面向用户的可执行单位是 Workflow（见 ``workflows/``）。

新增复杂流程：在 ``workflows/<id>/`` 导出 ``WORKFLOW``，再加入下方 ``WORKFLOWS``。
"""

from vision_workflow.flows.workflows.main import WORKFLOW as main_workflow
from vision_workflow.flows.workflows.zhan_yi_store import WORKFLOW as zhan_yi_store_workflow
from vision_workflow.module import Workflow

WORKFLOW = main_workflow  # CLI / 默认入口兼容

WORKFLOWS: list[Workflow] = [main_workflow, zhan_yi_store_workflow]


def get_workflow(workflow_id: str) -> Workflow:
    for wf in WORKFLOWS:
        if wf.id == workflow_id:
            return wf
    raise KeyError(f"未知复杂流程: {workflow_id}，可选: {[w.id for w in WORKFLOWS]}")


def workflow_choices() -> list[tuple[str, str]]:
    """UI 用：(display_name, workflow_id)。"""
    return [(w.display_name, w.id) for w in WORKFLOWS]
