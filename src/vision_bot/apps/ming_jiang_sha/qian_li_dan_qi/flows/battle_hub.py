"""三选一枢纽 mod 与画面重定位。"""

from __future__ import annotations

import time

from vision_bot.actions import click, do, move
from vision_bot.apps.ming_jiang_sha.paths import QLDQ
from vision_bot.perception.signal import Signal
from vision_bot.perception.snapshot import ScreenSnapshot, capture
from vision_bot.runtime.context import RunContext
from vision_bot.runtime.result import Result

HUB_DISMISS = "qldq.battle_hub.dismiss_up"
HUB_PICK_BATTLE = "qldq.battle_hub.pick_battle"
HUB_PICK_SHOP = "qldq.battle_hub.pick_shop"
HUB_PICK_EVENT = "qldq.battle_hub.pick_event"

CHOICE_REGION: tuple[int, int, int, int] = (800, 350, 1630, 780)
SIGNALS: dict[str, Signal] = {
    "choice.up_panel": Signal(template=f"{QLDQ}/battle_select/up.png"),
    "choice.challenge": Signal(template=f"{QLDQ}/battle_select/challenge.png", region=CHOICE_REGION),
    "choice.challenge_help": Signal(template=f"{QLDQ}/battle_select/challenge_help.png", region=CHOICE_REGION),
    "choice.yi_wai": Signal(template=f"{QLDQ}/battle_select/yi_wai.png", region=CHOICE_REGION),
    "choice.ba_qing_store": Signal(template=f"{QLDQ}/battle_select/ba_qing_store.png", region=CHOICE_REGION),
    "choice.pocket_event": Signal(template=f"{QLDQ}/battle_select/pocket_event.png", region=CHOICE_REGION),
    "choice.rest": Signal(template=f"{QLDQ}/battle_select/rest.png", region=CHOICE_REGION),
    "choice.lv_bu_wei_store": Signal(template=f"{QLDQ}/battle_select/lv_bu_wei_store.png", region=CHOICE_REGION),
    "choice.fei_fei": Signal(template=f"{QLDQ}/battle_select/fei_fei.png", region=CHOICE_REGION),
    "choice.shi_chang_shi": Signal(template=f"{QLDQ}/battle_select/shi_chang_shi.png", region=CHOICE_REGION),
    "choice.mo_zi": Signal(template=f"{QLDQ}/battle_select/mo_zi.png", region=CHOICE_REGION),
}

DETECT: set[str] = {
    "choice.up_panel",
    "choice.challenge",
    "choice.challenge_help",
    "choice.ba_qing_store",
    "choice.pocket_event",
    "choice.rest",
    "choice.lv_bu_wei_store",
    "choice.fei_fei",
    "choice.shi_chang_shi",
    "choice.mo_zi",
}


def detect(snap: ScreenSnapshot, ctx: RunContext | None = None) -> str | None:
    if snap.found("choice.up_panel"):
        return HUB_DISMISS
    if snap.found("choice.challenge") or snap.found("choice.challenge_help"):
        return HUB_PICK_BATTLE
    if snap.found("choice.yi_wai"):
        return HUB_PICK_BATTLE
    for k in ("choice.ba_qing_store", "choice.pocket_event", "choice.rest", "choice.lv_bu_wei_store"):
        if snap.found(k):
            return HUB_PICK_SHOP
    for k in ("choice.fei_fei", "choice.shi_chang_shi", "choice.mo_zi"):
        if snap.found(k):
            return HUB_PICK_EVENT
    return None


def relocate(ctx: RunContext) -> str | None:
    snap = capture(ctx.registry, ctx.base_dir, DETECT)
    return detect(snap, ctx)


def dismiss_up(ctx) -> Result:
    snap = ctx.snap({"choice.up_panel"})
    if snap.found("choice.up_panel"):
        do(move().to(1300, 1150).raw(), click())()
        time.sleep(0.4)
    return Result.fail("dispatch")
