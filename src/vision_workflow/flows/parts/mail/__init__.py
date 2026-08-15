"""子流程：收邮件。"""

from vision_workflow.actions.ming_jiang_sha import go_back, space_close
from vision_workflow.flows.parts.mail.actions import (
    click_email,
    click_one_click_receive,
)
from vision_workflow.module import Flow, Module, abort, onward, to
from vision_workflow.status import FULFILLED, REJECTED

_CLICK = {FULFILLED: onward, REJECTED: abort}
_OK = {FULFILLED: onward}

FLOW = Flow(
    id="mail",
    name="收邮件",
    description="领取邮箱内可一键领取的附件",
    entry="click_email",
    modules=[
        Module(id="click_email", name="打开邮箱", description="点击主界面邮箱入口", event=click_email, on=_CLICK),
        Module(
            id="one_click",
            name="一键领取",
            description="点击一键领取；未找到则回到打开邮箱",
            event=click_one_click_receive,
            on={FULFILLED: onward, REJECTED: to("click_email")},
        ),
        Module(id="space_click", name="关闭弹窗", description="Esc 关闭领取结果弹窗", event=space_close(), on=_OK),
        Module(id="email_close", name="返回", description="Esc 返回主界面", event=go_back(), on=_OK),
    ],
)
