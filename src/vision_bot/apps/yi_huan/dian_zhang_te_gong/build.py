"""组装店长特供 Flow。"""

from __future__ import annotations

from vision_bot.apps.yi_huan.dian_zhang_te_gong import steps as s
from vision_bot.runtime.builders import flow, mod
from vision_bot.runtime.flow import Flow


def build_dian_zhang_te_gong() -> Flow:
    return flow(
        id="dian_zhang_te_gong",
        name="店长特供",
        children=[
            mod(
                id="dian_zhang_te_gong.start",
                name="点开始至锤图标",
                active=s.click_start_until_cz,
            ),
            mod(
                id="dian_zhang_te_gong.tap_until_claim",
                name="连点至领取",
                active=s.tap_until_claim,
            ),
        ],
    )
