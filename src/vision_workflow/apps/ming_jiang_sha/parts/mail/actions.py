"""邮件流程动作。"""

from vision_workflow.apps.ming_jiang_sha.common.paths import DATA_ROOT
from vision_workflow.events import click, do, move
from vision_workflow.module import EventFn

_DIR = f"{DATA_ROOT}/mail"

click_email: EventFn = do(move().image(f"{_DIR}/email.png"), click())
click_one_click_receive: EventFn = do(
    move().image(f"{_DIR}/email_one_click_receive.png"), click()
)
