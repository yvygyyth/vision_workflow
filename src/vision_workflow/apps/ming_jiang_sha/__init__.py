"""名将杀应用：专属公共动作 + Flow 积木 + Workflow。"""

from vision_workflow.apps.ming_jiang_sha.workflows.main import WORKFLOW as main_workflow
from vision_workflow.apps.ming_jiang_sha.workflows.solo import WORKFLOWS as solo_workflows
from vision_workflow.module import Workflow

WORKFLOWS: list[Workflow] = [main_workflow, *solo_workflows]

__all__ = ["WORKFLOWS", "main_workflow"]
