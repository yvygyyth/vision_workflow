"""三选一枢纽。"""

from __future__ import annotations

import logging
import time

from vision_bot.actions import click, do, move
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.detect import relocate_hub
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.flows.pick_battle import build as build_pick_battle
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.flows.pick_event import build as build_pick_event
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.flows.pick_shop import build as build_pick_shop
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.signals import snap_found
from vision_bot.runtime.builders import flow, mod
from vision_bot.runtime.flow import Flow
from vision_bot.runtime.result import Result

logger = logging.getLogger(__name__)


def _dismiss_up(ctx) -> Result:
    snap = ctx.snap({"choice.up_panel"})
    if snap_found(snap, "choice.up_panel"):
        do(move().to(1300, 1150).raw(), click())(ctx.action_ctx())
        time.sleep(0.4)
    return Result.fail("dispatch")


def build() -> Flow:
    return flow(
        "qldq.battle_hub",
        "三选一枢纽",
        children=[
            mod("qldq.battle_hub.dismiss_up", "关闭上面板", _dismiss_up),
            build_pick_battle(),
            build_pick_shop(),
            build_pick_event(),
        ],
        relocate=[relocate_hub],
    )
