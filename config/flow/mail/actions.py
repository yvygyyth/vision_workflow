"""收邮件流程的专属事件。"""

from __future__ import annotations

from vision_workflow.events import click
from vision_workflow.module import EventFn

# 模板路径只服务本流程，改图只动这里
click_email: EventFn = click("data/samples/email.png")
click_one_click_receive: EventFn = click("data/samples/email_one_click_receive.png")
click_space_close: EventFn = click("data/samples/space-close.png")
