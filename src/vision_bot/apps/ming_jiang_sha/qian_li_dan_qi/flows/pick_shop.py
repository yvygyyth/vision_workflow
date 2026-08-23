"""商店三选一。"""

from __future__ import annotations

import logging
import time

from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.detect import qmod, relocate_pick_shop
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.signals import PICK_SHOP_DETECT, snap_center, snap_found
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.state import get_battle_state
from vision_bot.core.input import Mouse
from vision_bot.core.vision import grab_region, image_to_text
from vision_bot.runtime.builders import flow, mod
from vision_bot.runtime.flow import Flow
from vision_bot.runtime.result import Result

logger = logging.getLogger(__name__)

_COPPER_REGION = (1670, 20, 200, 50)


def _ocr_copper(ctx) -> int:
    text = image_to_text(grab_region(_COPPER_REGION))
    digits = "".join(c for c in (text or "") if c.isdigit())
    return int(digits) if digits else 0


def _choose(ctx) -> Result:
    snap = ctx.snap(PICK_SHOP_DETECT)
    state = get_battle_state(ctx)
    coins = _ocr_copper(ctx)
    state.copper_coins = coins
    logger.info("pick_shop 铜币=%s", coins)

    candidates: list[tuple[str, str]] = []
    if coins >= 30:
        candidates.append(("choice.ba_qing_store", "ba_qing_store"))
    candidates.extend(
        [
            ("choice.pocket_event", "pocket_event"),
            ("choice.rest", "rest"),
        ]
    )

    for key, outcome in candidates:
        c = snap_center(snap, key)
        if c:
            Mouse().move(*c).click(clicks=2).sleep(0.2).perform()
            logger.info("pick_shop 选中 %s", outcome)
            if outcome == "ba_qing_store":
                time.sleep(0.6)
                snap2 = ctx.snap({"choice.ba_qing_store"})
                if snap_found(snap2, "choice.ba_qing_store"):
                    ctx.goto(qmod("battle_hub.pick_shop", "verify_ba_qing"))
                    return Result.success()
                ctx.goto("qldq.ba_qing_store")
                return Result.success()
            ctx.goto(f"qldq.{outcome}")
            return Result.success()
    return Result.fail("商店选项均未识别")


def _verify_ba_qing(ctx) -> Result:
    time.sleep(0.4)
    snap = ctx.snap({"choice.ba_qing_store"})
    if snap_found(snap, "choice.ba_qing_store"):
        return Result.fail("巴清图标仍在")
    ctx.goto("qldq.ba_qing_store")
    return Result.success()


def build() -> Flow:
    return flow(
        "qldq.battle_hub.pick_shop",
        "商店选择",
        children=[
            mod("qldq.battle_hub.pick_shop.choose", "选商店", _choose),
            mod("qldq.battle_hub.pick_shop.verify_ba_qing", "验证巴清", _verify_ba_qing),
        ],
        relocate=[relocate_pick_shop],
    )
