"""子流程：收邮件。"""

from vision_workflow.flows.parts.mail.actions import (
    click_email,
    click_email_close,
    click_one_click_receive,
    click_space_close,
)
from vision_workflow.module import Flow, Module, abort, onward, to
from vision_workflow.status import FULFILLED, REJECTED

# 识图点击：找到 → 下一模块；未找到 → 失败结束本流程
_CLICK = {FULFILLED: onward, REJECTED: abort}

FLOW = Flow(
    id="mail",
    name="收邮件",
    entry="click_email",
    modules=[
        Module(id="click_email", event=click_email, on=_CLICK),
        Module(
            id="one_click",
            event=click_one_click_receive,
            # 未找到一键领取：跳回点邮箱（图循环）
            on={FULFILLED: onward, REJECTED: to("click_email")},
        ),
        Module(id="space_click", event=click_space_close, on=_CLICK),
        Module(id="email_close", event=click_email_close, on=_CLICK),
    ],
)
