"""组装千里单骑顶层 Flow。"""

from __future__ import annotations

from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.detect import relocate_qian_li
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.flows.ba_qing_store import build as build_ba_qing
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.flows.battle_hub import build as build_hub
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.flows.enter_battle import build as build_enter
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.flows.fei_fei import build as build_fei_fei
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.flows.fight import build as build_fight
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.flows.home_recovery import build as build_home
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.flows.mo_zi import build as build_mo_zi
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.flows.pocket_event import build as build_pocket
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.flows.rest import build as build_rest
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.flows.run_ended import build as build_run_ended
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.flows.shi_chang_shi import build as build_shi
from vision_bot.runtime.flow import Flow
from vision_bot.runtime.types import (
    BACK_TO_HUB,
    BA_QING_STORE,
    ENTER_BATTLE,
    FEI_FEI,
    FIGHT,
    MO_ZI,
    POCKET_EVENT,
    REST,
    RUN_ENDED,
    SHI_CHANG_SHI,
)


def build_qian_li_dan_qi() -> Flow:
    return Flow(
        id="qian_li_dan_qi",
        name="千里单骑",
        entry="enter_battle",
        relocate=relocate_qian_li,
        steps={
            "home_recovery": build_home(),
            "enter_battle": build_enter(),
            "battle_hub": build_hub(),
            "fight": build_fight(),
            "ba_qing_store": build_ba_qing(),
            "pocket_event": build_pocket(),
            "rest": build_rest(),
            "fei_fei": build_fei_fei(),
            "mo_zi": build_mo_zi(),
            "shi_chang_shi": build_shi(),
            "run_ended": build_run_ended(),
        },
        on={
            BACK_TO_HUB: "battle_hub",
            FIGHT: "fight",
            BA_QING_STORE: "ba_qing_store",
            POCKET_EVENT: "pocket_event",
            REST: "rest",
            FEI_FEI: "fei_fei",
            MO_ZI: "mo_zi",
            SHI_CHANG_SHI: "shi_chang_shi",
            RUN_ENDED: "run_ended",
            ENTER_BATTLE: "enter_battle",
        },
    )
