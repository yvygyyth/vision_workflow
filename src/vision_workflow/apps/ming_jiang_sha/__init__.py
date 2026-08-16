"""名将杀应用：专属公共动作 + Flow 积木 + Workflow。"""

from vision_workflow.apps.ming_jiang_sha.workflows.daily_free_resources import (
    WORKFLOW as daily_free_resources,
)
from vision_workflow.apps.ming_jiang_sha.workflows.qian_li_dan_qi import (
    WORKFLOW as qian_li_dan_qi,
)
from vision_workflow.apps.ming_jiang_sha.workflows.solo import WORKFLOWS as solo_workflows
from vision_workflow.module import Workflow

WORKFLOWS: list[Workflow] = [daily_free_resources, qian_li_dan_qi, *solo_workflows]

__all__ = ["WORKFLOWS", "daily_free_resources", "qian_li_dan_qi"]
