"""千里单骑根 Flow：全局画面重定位。"""

from __future__ import annotations

from vision_bot.apps.ming_jiang_sha.paths import COMMON_DIR, QLDQ
from vision_bot.perception.snapshot import capture_screen, match
from vision_bot.runtime.context import RunContext
from vision_bot.runtime.relocate import RelocateRule

_CHOICE_REGION = (800, 350, 1630, 780)
_CHOICE_TEMPLATES = (
    f"{QLDQ}/battle_select/challenge.png",
    f"{QLDQ}/battle_select/ba_qing_store.png",
    f"{QLDQ}/battle_select/pocket_event.png",
    f"{QLDQ}/battle_select/rest.png",
    f"{QLDQ}/battle_select/fei_fei.png",
    f"{QLDQ}/battle_select/yi_wai.png",
)


def _hit(ctx: RunContext, template: str, *, region=None) -> bool:
    return match(template, screenshot=capture_screen(), region=region).found


def _has_choice(ctx: RunContext) -> bool:
    return any(_hit(ctx, p, region=_CHOICE_REGION) for p in _CHOICE_TEMPLATES)


relocate: list[RelocateRule] = [
    RelocateRule(when=lambda ctx: _hit(ctx, f"{QLDQ}/enter_battle/switch.png"), then=None),
    RelocateRule(
        when=lambda ctx: _hit(ctx, f"{QLDQ}/enter_battle/battle_interface.png"),
        then=None,
    ),
    RelocateRule(
        when=lambda ctx: _hit(ctx, f"{QLDQ}/ba_qing_store/go_back.png"),
        then="qldq.ba_qing_store",
    ),
    RelocateRule(
        when=lambda ctx: _hit(ctx, f"{QLDQ}/fight/cancel.png")
        or _hit(ctx, f"{QLDQ}/fight/setting.png"),
        then="qldq.fight",
    ),
    RelocateRule(
        when=lambda ctx: _hit(ctx, f"{QLDQ}/pocket_event/event_patterm.png"),
        then="qldq.pocket_event",
    ),
    RelocateRule(
        when=lambda ctx: _hit(ctx, f"{QLDQ}/fei_fei/i_help_you.png"),
        then="qldq.fei_fei",
    ),
    RelocateRule(
        when=lambda ctx: _hit(ctx, f"{COMMON_DIR}/confirm.png") and _has_choice(ctx),
        then="qldq.battle_hub",
    ),
    RelocateRule(
        when=lambda ctx: _hit(ctx, f"{COMMON_DIR}/confirm.png"),
        then="qldq.run_ended",
    ),
    RelocateRule(when=_has_choice, then="qldq.battle_hub"),
    RelocateRule(
        when=lambda ctx: _hit(ctx, f"{QLDQ}/enter_battle/select_wu_jiang.png"),
        then="qldq.battle_select.enter_pick",
    ),
    RelocateRule(
        when=lambda ctx: _hit(ctx, f"{QLDQ}/enter_battle/start.png"),
        then="qldq.battle_select.enter_ready",
    ),
]
