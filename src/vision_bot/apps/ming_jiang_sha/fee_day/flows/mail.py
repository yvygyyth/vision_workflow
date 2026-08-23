"""收邮件。"""

from __future__ import annotations

from vision_bot.apps.ming_jiang_sha.actions import step_go_back, step_space_close
from vision_bot.apps.ming_jiang_sha.flow_helpers import do_click
from vision_bot.apps.ming_jiang_sha.paths import DATA_ROOT
from vision_bot.runtime.builders import flow, mod
from vision_bot.runtime.flow import Flow
from vision_bot.runtime.result import Result

_DIR = f"{DATA_ROOT}/mail"


def _relocate_mail(ctx) -> str | None:
    hit = ctx.action_ctx().find(f"{_DIR}/email.png", timeout=0.5)
    if hit.found:
        return "fee_day.mail.open"
    return None


def _one_click(ctx) -> Result:
    return do_click(ctx, f"{_DIR}/email_one_click_receive.png", timeout=5.0)


def build() -> Flow:
    return flow(
        "fee_day.mail",
        "收邮件",
        children=[
            mod("fee_day.mail.open", "打开邮箱", lambda ctx: do_click(ctx, f"{_DIR}/email.png")),
            mod("fee_day.mail.one_click", "一键领取", _one_click),
            mod("fee_day.mail.space_close", "关闭弹窗", step_space_close),
            mod("fee_day.mail.back", "返回", step_go_back),
        ],
        relocate=[_relocate_mail],
    )
