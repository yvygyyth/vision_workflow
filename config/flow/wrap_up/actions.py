"""收尾流程的自定义事件。"""

from __future__ import annotations

from vision_workflow.module import OK, ModuleContext


def action_log_done(m: ModuleContext) -> str:
    m.log("收尾模块执行完毕")
    return OK
