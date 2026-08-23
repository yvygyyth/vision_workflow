"""千里单骑 · 各 Flow 画面重定位（relocate）。"""

from __future__ import annotations

from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.signals import (
    ENTER_DETECT,
    FIGHT_DETECT,
    GLOBAL_DETECT,
    HUB_DETECT,
    PICK_BATTLE_DETECT,
    PICK_EVENT_DETECT,
    PICK_SHOP_DETECT,
    snap_found,
)
from vision_bot.perception.snapshot import ScreenSnapshot, capture
from vision_bot.runtime.context import RunContext

# hub step ids
HUB_DISMISS = "dismiss_up"
HUB_PICK_BATTLE = "pick_battle"
HUB_PICK_SHOP = "pick_shop"
HUB_PICK_EVENT = "pick_event"


def detect_qian_li(snap: ScreenSnapshot, ctx: RunContext | None = None) -> str | None:
    if snap_found(snap, "shop.go_back"):
        return "ba_qing_store"
    if snap_found(snap, "fight.cancel") or snap_found(snap, "fight.setting"):
        return "fight"
    if snap_found(snap, "pocket.event_pattern"):
        return "pocket_event"
    if snap_found(snap, "fei_fei.i_help_you"):
        return "fei_fei"
    if (
        snap_found(snap, "common.confirm")
        and not _choice_any(snap)
        and not snap_found(snap, "fight.cancel")
    ):
        return "run_ended"
    if _choice_any(snap) or snap_found(snap, "enter.battle_interface"):
        return "battle_hub"
    if snap_found(snap, "enter.start") or snap_found(snap, "enter.select_wu_jiang"):
        return "enter_battle"
    return None


def relocate_qian_li(ctx: RunContext) -> str | None:
    snap = capture(ctx.registry, ctx.base_dir, GLOBAL_DETECT)
    return detect_qian_li(snap, ctx)


def detect_hub(snap: ScreenSnapshot, ctx: RunContext | None = None) -> str | None:
    if snap_found(snap, "choice.up_panel"):
        return HUB_DISMISS
    if snap_found(snap, "choice.challenge") or snap_found(snap, "choice.challenge_help"):
        return HUB_PICK_BATTLE
    if snap_found(snap, "choice.yi_wai"):
        return HUB_PICK_BATTLE
    for k in ("choice.ba_qing_store", "choice.pocket_event", "choice.rest", "choice.lv_bu_wei_store"):
        if snap_found(snap, k):
            return HUB_PICK_SHOP
    for k in ("choice.fei_fei", "choice.shi_chang_shi", "choice.mo_zi"):
        if snap_found(snap, k):
            return HUB_PICK_EVENT
    return None


def relocate_hub(ctx: RunContext) -> str | None:
    snap = capture(ctx.registry, ctx.base_dir, HUB_DETECT)
    return detect_hub(snap, ctx)


def detect_pick_battle(snap: ScreenSnapshot, ctx: RunContext | None = None) -> str | None:
    if snap_found(snap, "choice.challenge_help"):
        return "choose"
    if snap_found(snap, "choice.challenge"):
        return "choose"
    if snap_found(snap, "choice.yi_wai"):
        return "choose_yi_wai"
    return None


def relocate_pick_battle(ctx: RunContext) -> str | None:
    snap = capture(ctx.registry, ctx.base_dir, PICK_BATTLE_DETECT)
    return detect_pick_battle(snap, ctx)


def detect_pick_shop(snap: ScreenSnapshot, ctx: RunContext | None = None) -> str | None:
    if any(
        snap_found(snap, k)
        for k in ("choice.ba_qing_store", "choice.pocket_event", "choice.rest", "choice.lv_bu_wei_store")
    ):
        return "choose"
    return None


def relocate_pick_shop(ctx: RunContext) -> str | None:
    snap = capture(ctx.registry, ctx.base_dir, PICK_SHOP_DETECT)
    return detect_pick_shop(snap, ctx)


def detect_pick_event(snap: ScreenSnapshot, ctx: RunContext | None = None) -> str | None:
    if any(snap_found(snap, k) for k in ("choice.fei_fei", "choice.shi_chang_shi", "choice.mo_zi")):
        return "choose"
    return None


def relocate_pick_event(ctx: RunContext) -> str | None:
    snap = capture(ctx.registry, ctx.base_dir, PICK_EVENT_DETECT)
    return detect_pick_event(snap, ctx)


def detect_enter(snap: ScreenSnapshot, ctx: RunContext | None = None) -> str | None:
    if snap_found(snap, "enter.battle_interface"):
        return "check_done"
    if snap_found(snap, "enter.start"):
        return "try_start"
    if snap_found(snap, "enter.select_wu_jiang"):
        return "select_wu_jiang"
    return "try_start"


def relocate_enter(ctx: RunContext) -> str | None:
    snap = capture(ctx.registry, ctx.base_dir, ENTER_DETECT)
    return detect_enter(snap, ctx)


def detect_fight(snap: ScreenSnapshot, ctx: RunContext | None = None) -> str | None:
    if snap_found(snap, "fight.cancel"):
        return "click_cancel"
    if snap_found(snap, "fight.setting"):
        return "click_setting"
    if snap_found(snap, "fight.challenge_end"):
        return "wait_end"
    if snap_found(snap, "fight.next_step"):
        return "next_step"
    return "click_cancel"


def relocate_fight(ctx: RunContext) -> str | None:
    snap = capture(ctx.registry, ctx.base_dir, FIGHT_DETECT)
    return detect_fight(snap, ctx)


def relocate_ba_qing_store(ctx: RunContext) -> str | None:
    snap = capture(ctx.registry, ctx.base_dir, {"shop.go_back"})
    if snap_found(snap, "shop.go_back"):
        return "go_back"
    return None


def relocate_shi_chang_shi(ctx: RunContext) -> str | None:
    snap = capture(ctx.registry, ctx.base_dir, {"shi_chang_shi.attack", "fight.cancel"})
    if snap_found(snap, "shi_chang_shi.attack"):
        return "attack"
    return "confirm"


def relocate_pocket_event(ctx: RunContext) -> str | None:
    return "check"


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
