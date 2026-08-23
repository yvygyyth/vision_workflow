"""三选一枢纽。"""

from __future__ import annotations

import logging
import time

from vision_bot.actions import click, do, move
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.detect import (
    HUB_DISMISS,
    HUB_PICK_BATTLE,
    HUB_PICK_EVENT,
    HUB_PICK_SHOP,
    relocate_hub,
)
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.flows.pick_battle import build as build_pick_battle
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.flows.pick_event import build as build_pick_event
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.flows.pick_shop import build as build_pick_shop
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.signals import snap_found
from vision_bot.runtime.flow import Flow, StepResult
from vision_bot.runtime.types import (
    BACK_TO_HUB,
    BA_QING_STORE,
    END,
    FEI_FEI,
    FIGHT,
    MO_ZI,
    POCKET_EVENT,
    REST,
    SHI_CHANG_SHI,
)

logger = logging.getLogger(__name__)


def _dismiss_up(ctx) -> StepResult:
    snap = ctx.snap({"choice.up_panel"})
    if snap_found(snap, "choice.up_panel"):
        do(move().to(1300, 1150).raw(), click())(ctx.action_ctx())
        time.sleep(0.4)
    return StepResult.fail("dispatch")


def build() -> Flow:
    return Flow(
        id="battle_hub",
        name="三选一枢纽",
        entry=HUB_DISMISS,
        relocate=relocate_hub,
        steps={
            HUB_DISMISS: _dismiss_up,
            HUB_PICK_BATTLE: build_pick_battle(),
            HUB_PICK_SHOP: build_pick_shop(),
            HUB_PICK_EVENT: build_pick_event(),
        },
        on={
            FIGHT: END,
            BA_QING_STORE: END,
            POCKET_EVENT: END,
            REST: END,
            FEI_FEI: END,
            MO_ZI: END,
            SHI_CHANG_SHI: END,
            BACK_TO_HUB: HUB_DISMISS,
        },
    )
