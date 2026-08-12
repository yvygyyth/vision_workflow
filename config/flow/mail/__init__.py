"""子流程：收邮件。"""

from config.flow.mail.actions import (
    click_email,
    click_email_close,
    click_one_click_receive,
    click_space_close,
)
from vision_workflow.module import Flow, Module

FLOW = Flow(
    id="mail",
    name="收邮件",
    entry="click_email",
    modules=[
        Module(id="click_email", event=click_email),
        Module(
            id="one_click",
            event=click_one_click_receive,
            fail="click_email",
        ),
        Module(id="space_click", event=click_space_close),
        Module(id="email_close", event=click_email_close),
    ],
    success="wrap_up",
)
