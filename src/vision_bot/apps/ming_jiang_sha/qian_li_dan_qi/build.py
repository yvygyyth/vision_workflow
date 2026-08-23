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
from vision_bot.runtime.builders import flow
from vision_bot.runtime.flow import Flow


def build_qian_li_dan_qi() -> Flow:
    return flow(
        "qldq",
        "千里单骑",
        children=[
            build_home(),
            build_enter(),
            build_hub(),
            build_fight(),
            build_ba_qing(),
            build_pocket(),
            build_rest(),
            build_fei_fei(),
            build_mo_zi(),
            build_shi(),
            build_run_ended(),
        ],
        relocate=[relocate_qian_li],
    )
