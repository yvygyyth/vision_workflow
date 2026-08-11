"""可复用的模块 action / judge。"""

from __future__ import annotations

from typing import Any

from vision_workflow.flow.context import FlowContext
from vision_workflow.promise import Settled


def action_click_email(ctx: FlowContext) -> Any:
    hit = ctx.find("data/samples/email.png", threshold=0.8, timeout=3)
    if not hit.found:
        return Settled.reject(hit.message, value=hit, feedback="未找到邮件图标")
    if hit.center:
        ctx.mouse().at(hit.center).click().sleep(0.2).perform()
    return hit


def judge_email_still_there(ctx: FlowContext, value: Any = None) -> bool | Settled:
    """示例判定：点完后是否还能看到邮件图标（请改成你的成功界面图）。"""
    hit = ctx.find("data/samples/email.png", threshold=0.8, timeout=5)
    if hit.found:
        return Settled.resolve(hit, feedback="确认出现 email.png")
    return Settled.reject("未确认到成功界面", feedback="未确认到 email.png")


def action_log_done(ctx: FlowContext) -> Any:
    ctx.log("收尾模块执行完毕")
    return True


def action_handle_fail(ctx: FlowContext) -> Any:
    ctx.log("进入失败处理模块")
    return Settled.reject("业务失败已处理", feedback="已执行失败模块")
