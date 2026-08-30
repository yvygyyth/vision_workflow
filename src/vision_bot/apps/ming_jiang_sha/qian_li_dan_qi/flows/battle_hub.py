"""三选一枢纽 mod 与画面重定位。"""

from __future__ import annotations

import logging
import time

from vision_bot.actions import click, do, move
from vision_bot.apps.ming_jiang_sha.paths import QLDQ
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.flows import fight
from vision_bot.vision import snap
from vision_bot.runtime.context import RunContext
from vision_bot.runtime.relocate import RelocateRule
from vision_bot.runtime.result import Result

logger = logging.getLogger(__name__)

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
ZHU_GE_LIANG = f"{QLDQ}/battle_select/zhu_ge_liang.png"
CANCEL = f"{QLDQ}/fight/cancel.png"
SETTING = f"{QLDQ}/fight/setting.png"

BATTLE_DETECT: set[str] = {CHALLENGE, CHALLENGE_HELP, YI_WAI}
SHOP_DETECT: set[str] = {BA_QING_STORE, POCKET_EVENT, REST, LV_BU_WEI_STORE}
EVENT_DETECT: set[str] = {FEI_FEI, SHI_CHANG_SHI, MO_ZI, ZHU_GE_LIANG}
IN_FIGHT_DETECT: set[str] = {CANCEL, SETTING}


def _has_in_fight(ctx: RunContext) -> bool:
    """已在战斗 UI（取消/设置）。锦囊等漏检时的兜底，须优先于上面板。"""
    return snap(IN_FIGHT_DETECT).race


def _has_up_panel(ctx: RunContext) -> bool:
    return snap(UP_PANEL).ok


def _has_battle(ctx: RunContext) -> bool:
    return snap(BATTLE_DETECT, region=CHOICE_REGION).race


def _has_shop(ctx: RunContext) -> bool:
    return snap(SHOP_DETECT, region=CHOICE_REGION).race


def _has_event(ctx: RunContext) -> bool:
    return snap(EVENT_DETECT, region=CHOICE_REGION).race


relocate: list[RelocateRule] = [
    # 漏进战斗时不能落到 dismiss_up（children[0]）死循环
    RelocateRule(when=_has_in_fight, then="qldq.battle_hub.recover_fight"),
    RelocateRule(when=_has_up_panel, then="qldq.battle_hub.dismiss_up"),
    RelocateRule(when=_has_battle, then="qldq.battle_hub.pick_battle"),
    RelocateRule(when=_has_shop, then="qldq.battle_hub.pick_shop"),
    RelocateRule(when=_has_event, then="qldq.battle_hub.pick_event"),
]


def recover_fight(ctx) -> Result:
    """枢纽上已见取消/设置：按无赠礼战斗打完再回三选一。"""
    logger.info("battle_hub → 已在战斗 UI，无赠礼战斗")
    return fight.run_battle_no_gift(ctx)


def dismiss_up(ctx) -> Result:
    if snap(UP_PANEL).ok:
        do(move().to(1300, 1150), click())()
        time.sleep(0.4)
    return Result.success(then="qldq.battle_hub")
