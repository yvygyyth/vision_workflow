"""收尾流程的自定义事件。"""

from __future__ import annotations

from typing import Any

from vision_workflow.flow.context import FlowContext


def action_log_done(ctx: FlowContext) -> Any:
    ctx.log("收尾模块执行完毕")
    return True
