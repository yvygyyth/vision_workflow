"""邮件流程动作。"""

from vision_workflow.events import click
from vision_workflow.module import EventFn

_DIR = "data/ming_jiang_sha/mail"

click_email: EventFn = click().image(f"{_DIR}/email.png").execute()
click_one_click_receive: EventFn = click().image(f"{_DIR}/email_one_click_receive.png").execute()
