"""妃妃事件。"""

from __future__ import annotations

import logging

from vision_bot.actions import click, do, move
from vision_bot.apps.ming_jiang_sha.actions import step_confirm
from vision_bot.runtime.builders import flow, mod
from vision_bot.runtime.flow import Flow
from vision_bot.runtime.result import Result

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
    act = ctx.action_ctx()
    for path in _OPTS:
        hit = act.find(path, timeout=0.8)
        if hit.found and hit.center:
            do(move().to(*hit.center).raw(), click())(act)
            return Result.success()
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
