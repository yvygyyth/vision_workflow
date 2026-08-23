"""组装每日免费资源顶层 Flow。"""

from __future__ import annotations

from vision_bot.apps.ming_jiang_sha.fee_day.flows.activity import build as build_activity
from vision_bot.apps.ming_jiang_sha.fee_day.flows.ba_qing_store import build as build_ba_qing
from vision_bot.apps.ming_jiang_sha.fee_day.flows.dang_qing_ge import build as build_dang
from vision_bot.apps.ming_jiang_sha.fee_day.flows.gong_hui import build as build_gong_hui
from vision_bot.apps.ming_jiang_sha.fee_day.flows.mail import build as build_mail
from vision_bot.apps.ming_jiang_sha.fee_day.flows.zhan_yi_store import build as build_zhan_yi
from vision_bot.apps.ming_jiang_sha.fee_day.flows.zhu_jiu_store import build as build_zhu_jiu
from vision_bot.runtime.builders import flow
from vision_bot.runtime.flow import Flow


def build_fee_day() -> Flow:
    return flow(
        "fee_day",
        "名将杀免费资源每日领取",
        children=[
            build_mail(),
            build_dang(),
            build_zhu_jiu(),
            build_zhan_yi(),
            build_ba_qing(),
            build_activity(),
            build_gong_hui(),
        ],
    )
