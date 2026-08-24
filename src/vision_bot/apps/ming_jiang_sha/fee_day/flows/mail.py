"""收邮件。"""

from __future__ import annotations

from vision_bot.apps.ming_jiang_sha.actions import step_go_back, step_space_close
from vision_bot.apps.ming_jiang_sha.flow_helpers import do_click
from vision_bot.apps.ming_jiang_sha.paths import DATA_ROOT
from vision_bot.runtime.builders import flow, mod
from vision_bot.runtime.flow import Flow
from vision_bot.runtime.result import Result
from vision_bot.vision import find

_DIR = f"{DATA_ROOT}/mail"
_ONE_CLICK = f"{_DIR}/email_one_click_receive.png"


def _open_mail(ctx) -> Result:
    if find(_ONE_CLICK, timeout=0.5).ok:
        return Result.success()
    return do_click(ctx, f"{_DIR}/email.png")


def _one_click(ctx) -> Result:
    return do_click(ctx, _ONE_CLICK, timeout=5.0)


def build() -> Flow:
    return flow(
        "fee_day.mail",
        "收邮件",
        children=[
            mod("fee_day.mail.open", "打开邮箱", _open_mail),
            mod("fee_day.mail.one_click", "一键领取", _one_click),
            mod("fee_day.mail.space_close", "关闭弹窗", step_space_close),
            mod("fee_day.mail.back", "返回", step_go_back),
        ],
    )
