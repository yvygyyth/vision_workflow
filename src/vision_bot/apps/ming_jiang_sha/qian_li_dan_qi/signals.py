"""千里单骑 · Signal 分组注册。"""

from __future__ import annotations

from vision_bot.apps.ming_jiang_sha.paths import COMMON_DIR, QLDQ
from vision_bot.perception.signal import Signal, SignalRegistry

CHOICE_REGION: tuple[int, int, int, int] = (800, 350, 1630, 780)

_TEMPLATES: dict[str, tuple[str, tuple[int, int, int, int] | None]] = {
    # 顶层 detect
    "enter.battle_interface": (f"{QLDQ}/enter_battle/battle_interface.png", None),
    "enter.start": (f"{QLDQ}/enter_battle/start.png", None),
    "common.confirm": (f"{COMMON_DIR}/confirm.png", None),
    "shop.go_back": (f"{QLDQ}/ba_qing_store/go_back.png", None),
    "fight.cancel": (f"{QLDQ}/fight/cancel.png", None),
    "fight.setting": (f"{QLDQ}/fight/setting.png", None),
    "fight.challenge_end": (f"{QLDQ}/fight/challenge_end.png", None),
    "fight.next_step": (f"{QLDQ}/fight/next_step.png", None),
    "fight.auto": (f"{QLDQ}/fight/auto.png", None),
    "pocket.event_pattern": (f"{QLDQ}/pocket_event/event_patterm.png", None),
    "pocket.ok": (f"{QLDQ}/pocket_event/ok.png", None),
    # hub
    "choice.up_panel": (f"{QLDQ}/battle_select/up.png", None),
    "choice.challenge": (f"{QLDQ}/battle_select/challenge.png", CHOICE_REGION),
    "choice.challenge_help": (f"{QLDQ}/battle_select/challenge_help.png", CHOICE_REGION),
    "choice.yi_wai": (f"{QLDQ}/battle_select/yi_wai.png", CHOICE_REGION),
    "choice.ba_qing_store": (f"{QLDQ}/battle_select/ba_qing_store.png", CHOICE_REGION),
    "choice.pocket_event": (f"{QLDQ}/battle_select/pocket_event.png", CHOICE_REGION),
    "choice.rest": (f"{QLDQ}/battle_select/rest.png", CHOICE_REGION),
    "choice.lv_bu_wei_store": (f"{QLDQ}/battle_select/lv_bu_wei_store.png", CHOICE_REGION),
    "choice.fei_fei": (f"{QLDQ}/battle_select/fei_fei.png", CHOICE_REGION),
    "choice.shi_chang_shi": (f"{QLDQ}/battle_select/shi_chang_shi.png", CHOICE_REGION),
    "choice.zhu_ge_liang": (f"{QLDQ}/battle_select/zhu_ge_liangf.png", CHOICE_REGION),
    "choice.mo_zi": (f"{QLDQ}/battle_select/mo_zi.png", CHOICE_REGION),
    # enter battle
    "enter.select_wu_jiang": (f"{QLDQ}/enter_battle/select_wu_jiang.png", None),
    "enter.search": (f"{QLDQ}/enter_battle/search.png", None),
    "enter.lv_bu": (f"{QLDQ}/enter_battle/lv_bu.png", None),
    # shop inner
    "shop.confirm": (f"{QLDQ}/ba_qing_store/confirm.png", None),
    "shop.no_buy": (f"{QLDQ}/ba_qing_store/no_buy.png", None),
    "shop.token_slot": (f"{QLDQ}/ba_qing_store/token_slot.png", None),
    # fei_fei inner
    "fei_fei.i_help_you": (f"{QLDQ}/fei_fei/i_help_you.png", None),
    "fei_fei.sleep": (f"{QLDQ}/fei_fei/sleep.png", None),
    "fei_fei.bargaining": (f"{QLDQ}/fei_fei/bargaining.png", None),
    # shi_chang_shi
    "shi_chang_shi.attack": (f"{QLDQ}/shi_chang_shi/attack.png", None),
    # fight gifts
    "fight.token": (f"{QLDQ}/fight/token.png", None),
    "fight.joint": (f"{QLDQ}/fight/joint.png", None),
    "fight.card": (f"{QLDQ}/fight/card.png", None),
    "fight.help": (f"{QLDQ}/fight/help.png", None),
    "fight.buff": (f"{QLDQ}/fight/buff.png", None),
}

GLOBAL_DETECT: set[str] = {
    "shop.go_back",
    "fight.cancel",
    "fight.setting",
    "common.confirm",
    "pocket.event_pattern",
    "choice.challenge",
    "choice.ba_qing_store",
    "choice.pocket_event",
    "choice.rest",
    "choice.fei_fei",
    "choice.shi_chang_shi",
    "choice.mo_zi",
    "choice.yi_wai",
    "enter.battle_interface",
    "enter.start",
    "fei_fei.i_help_you",
}

HUB_DETECT: set[str] = {
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

PICK_BATTLE_DETECT: set[str] = {
    "choice.challenge",
    "choice.challenge_help",
    "choice.yi_wai",
}

PICK_SHOP_DETECT: set[str] = {
    "choice.ba_qing_store",
    "choice.pocket_event",
    "choice.rest",
    "choice.lv_bu_wei_store",
}

PICK_EVENT_DETECT: set[str] = {
    "choice.fei_fei",
    "choice.shi_chang_shi",
    "choice.mo_zi",
}

FIGHT_DETECT: set[str] = {
    "fight.cancel",
    "fight.setting",
    "fight.challenge_end",
    "fight.next_step",
    "fight.auto",
    "common.confirm",
    "fight.token",
    "fight.joint",
}

ENTER_DETECT: set[str] = {
    "enter.battle_interface",
    "enter.start",
    "enter.select_wu_jiang",
    "enter.search",
}


def build_registry() -> SignalRegistry:
    reg = SignalRegistry()
    for sid, (template, region) in _TEMPLATES.items():
        reg.register(sid, Signal(template=template, region=region, threshold=0.8))
    return reg


def snap_found(snap, key: str) -> bool:
    hit = snap.hits.get(key)
    return hit is not None and hit.found


def snap_center(snap, key: str) -> tuple[int, int] | None:
    hit = snap.hits.get(key)
    if hit is None or not hit.found or not hit.center:
        return None
    return hit.center
