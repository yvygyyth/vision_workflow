"""墨子事件。"""

from __future__ import annotations

import logging
import random

from vision_bot.actions import click, do, move
from vision_bot.apps.ming_jiang_sha.actions import step_confirm
from vision_bot.runtime.builders import flow, mod
from vision_bot.runtime.flow import Flow
from vision_bot.runtime.result import Result

logger = logging.getLogger(__name__)

_OPTS = ((1130, 360), (1130, 630), (1130, 900))


def _confirm(ctx) -> Result:
    r = step_confirm(ctx)
    if not r.ok:
        ctx.goto("qldq.mo_zi.click")
    return r


def _click_option(ctx) -> Result:
    x, y = random.choice(_OPTS)
    do(move().to(x, y).raw(), click())(ctx.action_ctx())
    return Result.success()


def build() -> Flow:
    return flow(
        "qldq.mo_zi",
        "墨子",
        children=[
            mod("qldq.mo_zi.confirm", "确认", _confirm),
            mod("qldq.mo_zi.click", "点选项", _click_option),
        ],
    )
