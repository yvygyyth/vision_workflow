"""失败处理流程的自定义事件。"""

from __future__ import annotations

from typing import Any

from vision_workflow.flow.context import FlowContext
from vision_workflow.promise import Settled


def action_handle_fail(ctx: FlowContext) -> Any:
    ctx.log("进入失败处理模块")
    return Settled.reject("业务失败已处理", feedback="已执行失败模块")
