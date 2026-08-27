"""千里单骑根 Flow：全局画面重定位。"""

from __future__ import annotations

from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.signals import GLOBAL_DETECT
from vision_bot.perception.snapshot import ScreenSnapshot, capture
from vision_bot.runtime.context import RunContext


def detect(snap: ScreenSnapshot) -> str | None:
    if snap.found("shop.go_back"):
        return "qldq.ba_qing_store"
    if snap.found("fight.cancel") or snap.found("fight.setting"):
        return "qldq.fight"
    if snap.found("pocket.event_pattern"):
        return "qldq.pocket_event"
    if snap.found("fei_fei.i_help_you"):
        return "qldq.fei_fei"

    has_choice = any(
        snap.found(k)
        for k in (
            "choice.challenge",
            "choice.ba_qing_store",
            "choice.pocket_event",
            "choice.rest",
            "choice.fei_fei",
            "choice.yi_wai",
        )
    )
    if snap.found("common.confirm") and not has_choice and not snap.found("fight.cancel"):
        return "qldq.run_ended"
    if has_choice or snap.found("enter.battle_interface"):
        return "qldq.battle_hub"
    if snap.found("enter.select_wu_jiang"):
        return "qldq.battle_select.enter_pick"
    if snap.found("enter.start"):
        return "qldq.battle_select.enter_ready"
    return None


def relocate(ctx: RunContext) -> str | None:
    snap = capture(ctx.registry, ctx.base_dir, GLOBAL_DETECT)
    return detect(snap)
