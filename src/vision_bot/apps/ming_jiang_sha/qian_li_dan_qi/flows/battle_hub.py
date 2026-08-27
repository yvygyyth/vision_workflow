"""三选一枢纽 mod 与画面重定位。"""

from __future__ import annotations

import time

from vision_bot.actions import click, do, move
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.signals import HUB_DETECT, ensure_registry, snap_found
from vision_bot.perception.snapshot import ScreenSnapshot, capture
from vision_bot.runtime.context import RunContext
from vision_bot.runtime.result import Result

HUB_DISMISS = "qldq.battle_hub.dismiss_up"
HUB_PICK_BATTLE = "qldq.battle_hub.pick_battle"
HUB_PICK_SHOP = "qldq.battle_hub.pick_shop"
HUB_PICK_EVENT = "qldq.battle_hub.pick_event"


def detect(snap: ScreenSnapshot, ctx: RunContext | None = None) -> str | None:
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


def relocate(ctx: RunContext) -> str | None:
    ensure_registry(ctx)
    snap = capture(ctx.registry, ctx.base_dir, HUB_DETECT)
    return detect(snap, ctx)


def dismiss_up(ctx) -> Result:
    snap = ctx.snap({"choice.up_panel"})
    if snap_found(snap, "choice.up_panel"):
        do(move().to(1300, 1150).raw(), click())(ctx.action_ctx())
        time.sleep(0.4)
    return Result.fail("dispatch")
