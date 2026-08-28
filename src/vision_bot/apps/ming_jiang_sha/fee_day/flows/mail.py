"""收邮件。"""

from __future__ import annotations

from vision_bot.actions import click, do, move
from vision_bot.apps.ming_jiang_sha.paths import FEE_DAY
from vision_bot.runtime.result import Result
from vision_bot.vision import find

_ONE_CLICK = f"{FEE_DAY}/mail/email_one_click_receive.png"


def open(ctx) -> Result:
    if find(_ONE_CLICK, timeout=0.5).ok:
        return Result.success()
    return do(move().image(f"{FEE_DAY}/mail/email.png"), click())()


def one_click(ctx) -> Result:
    return do(move().image(_ONE_CLICK).match(timeout=5.0), click())()
