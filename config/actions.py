"""业务侧自定义事件（通用点击请用 vision_workflow.events.click）。"""

from __future__ import annotations

from typing import Any

from vision_workflow.flow.context import FlowContext
from vision_workflow.promise import Settled


def action_log_done(ctx: FlowContext) -> Any:
    ctx.log("收尾模块执行完毕")
    return True


def action_handle_fail(ctx: FlowContext) -> Any:
    ctx.log("进入失败处理模块")
    return Settled.reject("业务失败已处理", feedback="已执行失败模块")
