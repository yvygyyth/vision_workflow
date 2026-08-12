"""失败处理流程的自定义事件。"""

from __future__ import annotations

from vision_workflow.module import OK, ModuleContext


def action_handle_fail(m: ModuleContext) -> str:
    m.log("进入失败处理模块")
    return OK
