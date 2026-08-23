"""组装每日免费资源顶层 Flow。"""

from __future__ import annotations

from vision_bot.apps.ming_jiang_sha.fee_day.flows.activity import DONE as ACTIVITY_DONE
from vision_bot.apps.ming_jiang_sha.fee_day.flows.activity import build as build_activity
from vision_bot.apps.ming_jiang_sha.fee_day.flows.ba_qing_store import DONE as BA_QING_DONE
from vision_bot.apps.ming_jiang_sha.fee_day.flows.ba_qing_store import build as build_ba_qing
from vision_bot.apps.ming_jiang_sha.fee_day.flows.dang_qing_ge import DONE as DANG_DONE
from vision_bot.apps.ming_jiang_sha.fee_day.flows.dang_qing_ge import build as build_dang
from vision_bot.apps.ming_jiang_sha.fee_day.flows.gong_hui import DONE as GONG_HUI_DONE
from vision_bot.apps.ming_jiang_sha.fee_day.flows.gong_hui import build as build_gong_hui
from vision_bot.apps.ming_jiang_sha.fee_day.flows.mail import DONE as MAIL_DONE
from vision_bot.apps.ming_jiang_sha.fee_day.flows.mail import build as build_mail
from vision_bot.apps.ming_jiang_sha.fee_day.flows.zhan_yi_store import DONE as ZHAN_YI_DONE
from vision_bot.apps.ming_jiang_sha.fee_day.flows.zhan_yi_store import build as build_zhan_yi
from vision_bot.apps.ming_jiang_sha.fee_day.flows.zhu_jiu_store import DONE as ZHU_JIU_DONE
from vision_bot.apps.ming_jiang_sha.fee_day.flows.zhu_jiu_store import build as build_zhu_jiu
from vision_bot.runtime.flow import Flow
from vision_bot.runtime.types import END

_CHAIN: list[tuple[str, object, str]] = [
    ("mail", build_mail, MAIL_DONE),
    ("dang_qing_ge", build_dang, DANG_DONE),
    ("zhu_jiu_store", build_zhu_jiu, ZHU_JIU_DONE),
    ("zhan_yi_store", build_zhan_yi, ZHAN_YI_DONE),
    ("ba_qing_store", build_ba_qing, BA_QING_DONE),
    ("activity", build_activity, ACTIVITY_DONE),
    ("gong_hui", build_gong_hui, GONG_HUI_DONE),
]


def build_fee_day() -> Flow:
    steps: dict = {}
    on: dict = {}
    for i, (step_id, builder, done_key) in enumerate(_CHAIN):
        steps[step_id] = builder()
        if i + 1 < len(_CHAIN):
            on[done_key] = _CHAIN[i + 1][0]
    on[_CHAIN[-1][2]] = END
    return Flow(
        id="fee_day",
        name="名将杀免费资源每日领取",
        entry=_CHAIN[0][0],
        steps=steps,
        on=on,
    )
