"""巴清商店（简化）。"""

from __future__ import annotations

import logging
import time

from vision_bot.actions import click, do, move
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.detect import relocate_ba_qing_store
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.signals import snap_found
from vision_bot.runtime.builders import flow, mod
from vision_bot.runtime.flow import Flow
from vision_bot.runtime.result import Result

logger = logging.getLogger(__name__)


def _go_back(ctx) -> Result:
    do(move().image("data/ming_jiang_sha/qian_li_dan_qi/ba_qing_store/go_back.png"), click())(
        ctx.action_ctx()
    )
    return Result.success()


def _confirm(ctx) -> Result:
    do(move().image("data/ming_jiang_sha/qian_li_dan_qi/ba_qing_store/confirm.png"), click())(
        ctx.action_ctx()
    )
    return Result.success()


def _ensure_left(ctx) -> Result:
    time.sleep(0.6)
    snap = ctx.snap({"shop.go_back"})
    if snap_found(snap, "shop.go_back"):
        return Result.fail("仍在店内")
    return Result.success()


def build() -> Flow:
    return flow(
        "qldq.ba_qing_store",
        "巴清商店",
        children=[
            mod("qldq.ba_qing_store.go_back", "返回", _go_back),
            mod("qldq.ba_qing_store.confirm", "确认", _confirm),
            mod("qldq.ba_qing_store.ensure_left", "确认离店", _ensure_left),
        ],
        relocate=[relocate_ba_qing_store],
    )
