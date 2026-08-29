"""三选一枢纽 mod 与画面重定位。"""

from __future__ import annotations

import time

from vision_bot.actions import click, do, move
from vision_bot.apps.ming_jiang_sha.paths import QLDQ
from vision_bot.perception.snapshot import ScreenSnapshot, capture_screen, match, snap
from vision_bot.runtime.context import RunContext
from vision_bot.runtime.relocate import RelocateRule
from vision_bot.runtime.result import Result

HUB_DISMISS = "qldq.battle_hub.dismiss_up"
HUB_PICK_BATTLE = "qldq.battle_hub.pick_battle"
HUB_PICK_SHOP = "qldq.battle_hub.pick_shop"
HUB_PICK_EVENT = "qldq.battle_hub.pick_event"

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

_CHOICE_DETECT = (
    CHALLENGE,
    CHALLENGE_HELP,
    YI_WAI,
    BA_QING_STORE,
    POCKET_EVENT,
    REST,
    LV_BU_WEI_STORE,
    FEI_FEI,
    SHI_CHANG_SHI,
    MO_ZI,
)


_HUB_SHOT = "_battle_hub_relocate_shot"


def _hub_shot(ctx: RunContext) -> ScreenSnapshot:
    shot = ctx.vars.get(_HUB_SHOT)
    if shot is None:
        frame = capture_screen()
        hits = {UP_PANEL: match(UP_PANEL, screenshot=frame)}
        for path in _CHOICE_DETECT:
            hits[path] = match(path, screenshot=frame, region=CHOICE_REGION)
        shot = ScreenSnapshot(hits=hits, image=frame)
        ctx.vars[_HUB_SHOT] = shot
    return shot


relocate: list[RelocateRule] = [
    RelocateRule(when=lambda ctx: _hub_shot(ctx).found(UP_PANEL), then=HUB_DISMISS),
    RelocateRule(
        when=lambda ctx: _hub_shot(ctx).found(CHALLENGE)
        or _hub_shot(ctx).found(CHALLENGE_HELP)
        or _hub_shot(ctx).found(YI_WAI),
        then=HUB_PICK_BATTLE,
    ),
    RelocateRule(
        when=lambda ctx: any(
            _hub_shot(ctx).found(p)
            for p in (BA_QING_STORE, POCKET_EVENT, REST, LV_BU_WEI_STORE)
        ),
        then=HUB_PICK_SHOP,
    ),
    RelocateRule(
        when=lambda ctx: any(
            _hub_shot(ctx).found(p) for p in (FEI_FEI, SHI_CHANG_SHI, MO_ZI)
        ),
        then=HUB_PICK_EVENT,
    ),
]


def dismiss_up(ctx) -> Result:
    shot = snap({UP_PANEL})
    if shot.found(UP_PANEL):
        do(move().to(1300, 1150).raw(), click())()
        time.sleep(0.4)
    return Result.fail("dispatch")
