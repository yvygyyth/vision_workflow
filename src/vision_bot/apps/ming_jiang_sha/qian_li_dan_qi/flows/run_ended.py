"""本轮结束。"""

from __future__ import annotations

from vision_bot.apps.ming_jiang_sha.actions import step_confirm
from vision_bot.events import press_esc
from vision_bot.runtime.builders import flow, mod
from vision_bot.runtime.flow import Flow
from vision_bot.runtime.result import Result


def _confirm(ctx) -> Result:
    r = step_confirm(ctx)
    if not r.ok:
        ctx.goto("qldq.run_ended.close")
    return r


def _close(ctx) -> Result:
    press_esc(cancelled=ctx.cancelled, times=2)
    ctx.goto("qldq.enter_battle")
    return Result.success()


def build() -> Flow:
    return flow(
        "qldq.run_ended",
        "本轮结束",
        children=[
            mod("qldq.run_ended.confirm", "确认", _confirm),
            mod("qldq.run_ended.close", "关闭", _close),
        ],
    )
