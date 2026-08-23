"""巴清商店（简化）。"""

from __future__ import annotations

import logging
import time

from vision_bot.actions import click, do, move
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.detect import relocate_ba_qing_store
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.signals import snap_found
from vision_bot.runtime.flow import Flow, StepResult
from vision_bot.runtime.types import BACK_TO_HUB, END

logger = logging.getLogger(__name__)


def _go_back(ctx) -> StepResult:
    do(move().image("data/ming_jiang_sha/qian_li_dan_qi/ba_qing_store/go_back.png"), click())(
        ctx.action_ctx()
    )
    return StepResult.ok(next_id="confirm")


def _confirm(ctx) -> StepResult:
    do(move().image("data/ming_jiang_sha/qian_li_dan_qi/ba_qing_store/confirm.png"), click())(
        ctx.action_ctx()
    )
    return StepResult.ok(next_id="ensure_left")


def _ensure_left(ctx) -> StepResult:
    time.sleep(0.6)
    snap = ctx.snap({"shop.go_back"})
    if snap_found(snap, "shop.go_back"):
        return StepResult.fail("仍在店内")
    return StepResult.end(BACK_TO_HUB)


def build() -> Flow:
    return Flow(
        id="ba_qing_store",
        name="巴清商店",
        entry="go_back",
        relocate=relocate_ba_qing_store,
        steps={
            "go_back": _go_back,
            "confirm": _confirm,
            "ensure_left": _ensure_left,
        },
        on={BACK_TO_HUB: END},
    )
