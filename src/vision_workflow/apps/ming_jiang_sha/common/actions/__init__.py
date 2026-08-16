"""名将杀专属公共动作：Esc 语义 + common 模板点击。

::

    from vision_workflow.apps.ming_jiang_sha.common.actions import space_close, go_back, confirm
"""

from vision_workflow.apps.ming_jiang_sha.common.actions.clicks import (
    click_confirm,
    click_ling_xi_box,
    click_max,
    click_ming_jiang_ce,
    confirm,
)
from vision_workflow.apps.ming_jiang_sha.common.actions.go_back import go_back
from vision_workflow.apps.ming_jiang_sha.common.actions.space_close import space_close

__all__ = [
    "confirm",
    "click_confirm",
    "click_max",
    "click_ming_jiang_ce",
    "click_ling_xi_box",
    "go_back",
    "space_close",
]
