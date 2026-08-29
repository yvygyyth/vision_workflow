"""三选一枢纽 mod 与画面重定位。"""

from __future__ import annotations

import time

from vision_bot.actions import click, do, move
from vision_bot.apps.ming_jiang_sha.paths import QLDQ
from vision_bot.vision import snap
from vision_bot.runtime.context import RunContext
from vision_bot.runtime.relocate import RelocateRule
from vision_bot.runtime.result import Result

CHOICE_REGION: tuple[int, int, int, int] = (800, 350, 1630, 780)

UP_PANEL = f"{QLDQ}/battle_select/up.png"
CHALLENGE = f"{QLDQ}/battle_select/challenge.png"
CHALLENGE_HELP = f"{QLDQ}/battle_select/challenge_help.png"
YI_WAI = f"{QLDQ}/battle_select/yi_wai.png"
BA_QING_STORE = f"{QLDQ}/battle_select/ba_qing_store.png"
POCKET_EVENT = f"{QLDQ}/battle_select/pocket_event.png"
REST = f"{QLDQ}/battle_select/rest.png"
LV_BU_WEI_STORE = f"{QLDQ}/battle_select/lv_bu_wei_store.png"
FEI_FEI = f"{QLDQ}/battle_select/fei_fei.png"
SHI_CHANG_SHI = f"{QLDQ}/battle_select/shi_chang_shi.png"
MO_ZI = f"{QLDQ}/battle_select/mo_zi.png"

BATTLE_DETECT: set[str] = {CHALLENGE, CHALLENGE_HELP, YI_WAI}
SHOP_DETECT: set[str] = {BA_QING_STORE, POCKET_EVENT, REST, LV_BU_WEI_STORE}
EVENT_DETECT: set[str] = {FEI_FEI, SHI_CHANG_SHI, MO_ZI}


def _has_up_panel(ctx: RunContext) -> bool:
    return snap(UP_PANEL).ok


def _has_battle(ctx: RunContext) -> bool:
    return snap(BATTLE_DETECT, region=CHOICE_REGION).race


def _has_shop(ctx: RunContext) -> bool:
    return snap(SHOP_DETECT, region=CHOICE_REGION).race


def _has_event(ctx: RunContext) -> bool:
    return snap(EVENT_DETECT, region=CHOICE_REGION).race


relocate: list[RelocateRule] = [
    RelocateRule(when=_has_up_panel, then="qldq.battle_hub.dismiss_up"),
    RelocateRule(when=_has_battle, then="qldq.battle_hub.pick_battle"),
    RelocateRule(when=_has_shop, then="qldq.battle_hub.pick_shop"),
    RelocateRule(when=_has_event, then="qldq.battle_hub.pick_event"),
]


def dismiss_up(ctx) -> Result:
    if snap(UP_PANEL).ok:
        do(move().to(1300, 1150), click())()
        time.sleep(0.4)
    return Result.success()
