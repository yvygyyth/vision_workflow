"""本轮结束 mod。"""

from __future__ import annotations

from vision_bot.apps.ming_jiang_sha.actions import step_confirm
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.state import clear_battle_state
from vision_bot.events import press_esc
from vision_bot.runtime.result import Result


def confirm(ctx) -> Result:
    r = step_confirm(ctx)
    if not r.ok:
        ctx.goto("qldq.run_ended.close")
    return r


def close(ctx) -> Result:
    press_esc(times=2)
    clear_battle_state(ctx)
    ctx.goto("qldq.battle_select.enter_ready")
    return Result.success()
