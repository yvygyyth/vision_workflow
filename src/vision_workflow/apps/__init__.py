"""应用目录：各自动化对象的业务编排（相对框架公共代码）。

- 框架：``vision_workflow`` 根下 module / events / flow / ui …
- 应用：``apps/<app_id>/``（common + parts + workflows）

CLI / UI 只从本包取 ``WORKFLOWS``。
"""

from vision_workflow.apps.ming_jiang_sha import WORKFLOWS as ming_jiang_sha_workflows
from vision_workflow.apps.ming_jiang_sha.workflows.main import WORKFLOW as main_workflow
from vision_workflow.module import Workflow

WORKFLOW = main_workflow  # CLI / 默认入口兼容

WORKFLOWS: list[Workflow] = [*ming_jiang_sha_workflows]


def get_workflow(workflow_id: str) -> Workflow:
    for wf in WORKFLOWS:
        if wf.id == workflow_id:
            return wf
    raise KeyError(f"未知复杂流程: {workflow_id}，可选: {[w.id for w in WORKFLOWS]}")


def workflow_choices() -> list[tuple[str, str]]:
    """UI 用：(display_name, workflow_id)。"""
    return [(w.display_name, w.id) for w in WORKFLOWS]


__all__ = [
    "WORKFLOW",
    "WORKFLOWS",
    "get_workflow",
    "workflow_choices",
]
