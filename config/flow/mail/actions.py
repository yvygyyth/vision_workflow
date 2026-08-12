"""收邮件流程的专属事件。"""

from __future__ import annotations

from vision_workflow.events import click
from vision_workflow.module import EventFn

# 模板图放在 data/samples/<流程id>/
click_email: EventFn = click("data/samples/mail/email.png")
click_one_click_receive: EventFn = click("data/samples/mail/email_one_click_receive.png")
click_space_close: EventFn = click("data/samples/mail/space-close.png")
