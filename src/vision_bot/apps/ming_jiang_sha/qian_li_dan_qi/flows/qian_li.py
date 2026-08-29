"""千里单骑根 Flow：全局画面重定位。"""

from __future__ import annotations

from collections.abc import Callable

from vision_bot.perception.snapshot import capture_screen, match_signal
from vision_bot.runtime.context import RunContext
from vision_bot.runtime.jump import Relocate

_CHOICE_KEYS = (
    "choice.challenge",
    "choice.ba_qing_store",
    "choice.pocket_event",
    "choice.rest",
    "choice.fei_fei",
    "choice.yi_wai",
)


def route(found: Callable[[str], bool]) -> str | Relocate | None:
    """根据「是否找到某图」决定跳转目标（纯路由，不含截屏）。"""
    if found("enter.battle_interface"):
        return None
    if found("shop.go_back"):
        return "qldq.ba_qing_store"
    if found("fight.cancel") or found("fight.setting"):
        return "qldq.fight"
    if found("pocket.event_pattern"):
        return "qldq.pocket_event"
    if found("fei_fei.i_help_you"):
        return "qldq.fei_fei"

    has_choice = any(found(k) for k in _CHOICE_KEYS)
    if found("common.confirm") and not has_choice:
        return "qldq.run_ended"
    if has_choice:
        return "qldq.battle_hub"
    if found("enter.select_wu_jiang"):
        return "qldq.battle_select.enter_pick"
    if found("enter.start"):
        return "qldq.battle_select.enter_ready"
    return Relocate.PARENT


def relocate(ctx: RunContext) -> str | Relocate | None:
    """截一帧 → 按优先级逐张匹配 → 命中则返回对应 id。"""
    img = capture_screen()
    cache: dict[str, bool] = {}

    def found(signal_id: str) -> bool:
        if signal_id not in cache:
            cache[signal_id] = match_signal(
                ctx.registry, ctx.base_dir, signal_id, screenshot=img
            ).found
        return cache[signal_id]

    return route(found)
