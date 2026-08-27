"""千里单骑根 Flow：全局画面重定位。"""

from __future__ import annotations

from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.signals import (
    GLOBAL_DETECT,
    ensure_registry,
    snap_found,
)
from vision_bot.perception.snapshot import ScreenSnapshot, capture
from vision_bot.runtime.context import RunContext


def detect(snap: ScreenSnapshot, ctx: RunContext | None = None) -> str | None:
    if snap_found(snap, "shop.go_back"):
        return "qldq.ba_qing_store"
    if snap_found(snap, "fight.cancel") or snap_found(snap, "fight.setting"):
        return "qldq.fight"
    if snap_found(snap, "pocket.event_pattern"):
        return "qldq.pocket_event"
    if snap_found(snap, "fei_fei.i_help_you"):
        return "qldq.fei_fei"
    if (
        snap_found(snap, "common.confirm")
        and not _choice_any(snap)
        and not snap_found(snap, "fight.cancel")
    ):
        return "qldq.run_ended"
    if _choice_any(snap) or snap_found(snap, "enter.battle_interface"):
        return "qldq.battle_hub"
    if snap_found(snap, "enter.select_wu_jiang"):
        return "qldq.battle_select.enter_pick"
    if snap_found(snap, "enter.start"):
        return "qldq.battle_select.enter_ready"
    return None


def relocate(ctx: RunContext) -> str | None:
    ensure_registry(ctx)
    snap = capture(ctx.registry, ctx.base_dir, GLOBAL_DETECT)
    return detect(snap, ctx)


def _choice_any(snap: ScreenSnapshot) -> bool:
    keys = (
        "choice.challenge",
        "choice.ba_qing_store",
        "choice.pocket_event",
        "choice.rest",
        "choice.fei_fei",
        "choice.yi_wai",
    )
    return any(snap_found(snap, k) for k in keys)
