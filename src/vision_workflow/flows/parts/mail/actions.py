"""收邮件流程的专属事件。"""

from __future__ import annotations

from vision_workflow.events import click_image
from vision_workflow.module import EventFn

_DIR = "data/ming_jiang_sha/mail"

click_email: EventFn = click_image(f"{_DIR}/email.png")
click_one_click_receive: EventFn = click_image(f"{_DIR}/email_one_click_receive.png")
click_space_close: EventFn = click_image(f"{_DIR}/space-close.png")
click_email_close: EventFn = click_image(f"{_DIR}/email-close.png")
