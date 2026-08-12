"""收邮件流程的专属事件。"""

from __future__ import annotations

from vision_workflow.events import click
from vision_workflow.module import EventFn

# 模板图放在 data/ming_jiang_sha/<流程id>/
click_email: EventFn = click("data/ming_jiang_sha/mail/email.png")
click_one_click_receive: EventFn = click("data/ming_jiang_sha/mail/email_one_click_receive.png")
click_space_close: EventFn = click("data/ming_jiang_sha/mail/space-close.png")
click_email_close: EventFn = click("data/ming_jiang_sha/mail/email-close.png")
