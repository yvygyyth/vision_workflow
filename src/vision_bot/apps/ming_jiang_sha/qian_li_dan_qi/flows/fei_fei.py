"""妃妃事件。"""

from __future__ import annotations

import logging

from vision_bot.apps.ming_jiang_sha.actions import step_confirm
from vision_bot.events import click_match
from vision_bot.runtime.builders import flow, mod
from vision_bot.runtime.flow import Flow
from vision_bot.runtime.result import Result
from vision_bot.vision import find

logger = logging.getLogger(__name__)

_OPTS = (
    "data/ming_jiang_sha/qian_li_dan_qi/fei_fei/i_help_you.png",
    "data/ming_jiang_sha/qian_li_dan_qi/fei_fei/sleep.png",
    "data/ming_jiang_sha/qian_li_dan_qi/fei_fei/bargaining.png",
)


def _confirm(ctx) -> Result:
    r = step_confirm(ctx)
    if not r.ok:
        ctx.goto("qldq.fei_fei.choose")
    return r


def _choose(ctx) -> Result:
    for path in _OPTS:
        result = find(path, base_dir=ctx.base_dir, cancelled=ctx.cancelled, timeout=0.8)
        if result.ok:
            return click_match(result.value)
    return Result.fail("妃妃选项未识别")


def build() -> Flow:
    return flow(
        "qldq.fei_fei",
        "妃妃",
        children=[
            mod("qldq.fei_fei.confirm", "确认", _confirm),
            mod("qldq.fei_fei.choose", "选择", _choose),
        ],
    )
