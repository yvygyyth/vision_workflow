"""商店三选一。"""

from __future__ import annotations

import logging
import time

from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.detect import relocate_pick_shop
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.signals import PICK_SHOP_DETECT, snap_center, snap_found
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.state import get_battle_state
from vision_bot.core.input import Mouse
from vision_bot.core.vision import grab_region, image_to_text
from vision_bot.runtime.flow import Flow, StepResult
from vision_bot.runtime.types import BA_QING_STORE, END, POCKET_EVENT, REST, STILL_HERE

logger = logging.getLogger(__name__)

_COPPER_REGION = (1670, 20, 200, 50)


def _ocr_copper(ctx) -> int:
    text = image_to_text(grab_region(_COPPER_REGION))
    digits = "".join(c for c in (text or "") if c.isdigit())
    return int(digits) if digits else 0


def _choose(ctx) -> StepResult:
    snap = ctx.snap(PICK_SHOP_DETECT)
    state = get_battle_state(ctx)
    coins = _ocr_copper(ctx)
    state.copper_coins = coins
    logger.info("pick_shop 铜币=%s", coins)

    candidates: list[tuple[str, str]] = []
    if coins >= 30:
        candidates.append(("choice.ba_qing_store", BA_QING_STORE))
    candidates.extend(
        [
            ("choice.pocket_event", POCKET_EVENT),
            ("choice.rest", REST),
        ]
    )

    for key, outcome in candidates:
        c = snap_center(snap, key)
        if c:
            Mouse().move(*c).click(clicks=2).sleep(0.2).perform()
            logger.info("pick_shop 选中 %s", outcome)
            if outcome == BA_QING_STORE:
                time.sleep(0.6)
                snap2 = ctx.snap({"choice.ba_qing_store"})
                if snap_found(snap2, "choice.ba_qing_store"):
                    return StepResult.ok(outcome=STILL_HERE, next_id="verify_ba_qing")
                return StepResult.end(BA_QING_STORE)
            return StepResult.end(outcome)
    return StepResult.fail("商店选项均未识别")


def _verify_ba_qing(ctx) -> StepResult:
    time.sleep(0.4)
    snap = ctx.snap({"choice.ba_qing_store"})
    if snap_found(snap, "choice.ba_qing_store"):
        return StepResult.fail("巴清图标仍在")
    return StepResult.end(BA_QING_STORE)


def build() -> Flow:
    return Flow(
        id="pick_shop",
        name="商店选择",
        entry="choose",
        relocate=relocate_pick_shop,
        steps={
            "choose": _choose,
            "verify_ba_qing": _verify_ba_qing,
        },
        on={
            BA_QING_STORE: END,
            POCKET_EVENT: END,
            REST: END,
            STILL_HERE: "choose",
        },
    )
