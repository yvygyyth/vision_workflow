"""收邮件。"""

from __future__ import annotations

from vision_bot.apps.ming_jiang_sha.actions import step_go_back, step_space_close
from vision_bot.apps.ming_jiang_sha.flow_helpers import do_click
from vision_bot.apps.ming_jiang_sha.paths import DATA_ROOT
from vision_bot.runtime.flow import Flow, StepResult
from vision_bot.runtime.types import FAIL

_DIR = f"{DATA_ROOT}/mail"
DONE = "mail_done"


def _click_email(ctx) -> StepResult:
    return do_click(ctx, f"{_DIR}/email.png")


def _one_click(ctx) -> StepResult:
    return do_click(ctx, f"{_DIR}/email_one_click_receive.png", timeout=5.0)


def _finish(ctx) -> StepResult:
    step_go_back(ctx)
    return StepResult.end(DONE)


def build() -> Flow:
    return Flow(
        id="mail",
        name="收邮件",
        entry="click_email",
        steps={
            "click_email": _click_email,
            "one_click": _one_click,
            "space_close": step_space_close,
            "go_back": _finish,
        },
        routes={
            "one_click": {FAIL: "click_email"},
        },
    )
