"""千里单骑根 Flow：全局画面重定位。"""

from __future__ import annotations

from vision_bot.apps.ming_jiang_sha.paths import COMMON_DIR, QLDQ
from vision_bot.perception.snapshot import capture_screen, match
from vision_bot.runtime.context import RunContext
from vision_bot.runtime.jump import Relocate

_CHOICE_REGION = (800, 350, 1630, 780)
_CHOICE_TEMPLATES = (
    f"{QLDQ}/battle_select/challenge.png",
    f"{QLDQ}/battle_select/ba_qing_store.png",
    f"{QLDQ}/battle_select/pocket_event.png",
    f"{QLDQ}/battle_select/rest.png",
    f"{QLDQ}/battle_select/fei_fei.png",
    f"{QLDQ}/battle_select/yi_wai.png",
)


def relocate(ctx: RunContext) -> str | Relocate | None:
    """截一帧 → 按优先级逐张匹配 → 命中则返回对应 id。"""
    frame = capture_screen()

    def hit(template: str, *, region=None) -> bool:
        return match(template, screenshot=frame, region=region).found

    def has_choice() -> bool:
        return any(hit(p, region=_CHOICE_REGION) for p in _CHOICE_TEMPLATES)
        
    if hit(f"{QLDQ}/enter_battle/switch.png"):
        return None
    if hit(f"{QLDQ}/enter_battle/battle_interface.png"):
        return None
    if hit(f"{QLDQ}/ba_qing_store/go_back.png"):
        return "qldq.ba_qing_store"
    if hit(f"{QLDQ}/fight/cancel.png") or hit(f"{QLDQ}/fight/setting.png"):
        return "qldq.fight"
    if hit(f"{QLDQ}/pocket_event/event_patterm.png"):
        return "qldq.pocket_event"
    if hit(f"{QLDQ}/fei_fei/i_help_you.png"):
        return "qldq.fei_fei"

    # confirm 在结算和三选一面板都会出现：有 choice 图 → hub，否则 → 跑完
    if hit(f"{COMMON_DIR}/confirm.png"):
        if has_choice():
            return "qldq.battle_hub"
        return "qldq.run_ended"

    if has_choice():
        return "qldq.battle_hub"
    if hit(f"{QLDQ}/enter_battle/select_wu_jiang.png"):
        return "qldq.battle_select.enter_pick"
    if hit(f"{QLDQ}/enter_battle/start.png"):
        return "qldq.battle_select.enter_ready"
    return Relocate.PARENT
