"""商店三选一 mod。"""

from __future__ import annotations

import logging
import time

from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.flows.battle_hub import (
    BA_QING_STORE,
    CHOICE_REGION,
    LV_BU_WEI_STORE,
    POCKET_EVENT,
    REST,
)
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.state import get_battle_state
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.utils.bag import refresh_copper_coins
from vision_bot.core.input import Mouse
from vision_bot.perception.snapshot import ScreenSnapshot, snap
from vision_bot.runtime.context import RunContext
from vision_bot.runtime.relocate import RelocateRule
from vision_bot.runtime.result import Result

logger = logging.getLogger(__name__)

DETECT: set[str] = {BA_QING_STORE, POCKET_EVENT, REST, LV_BU_WEI_STORE}


def _has_shop_choice(ctx: RunContext) -> bool:
    shot = snap(DETECT, region=CHOICE_REGION)
    return any(shot.found(p) for p in DETECT)


relocate: list[RelocateRule] = [
    RelocateRule(when=_has_shop_choice, then="qldq.battle_hub.pick_shop.choose"),
]


def choose(ctx) -> Result:
    shot = snap(DETECT, region=CHOICE_REGION)
    state = get_battle_state(ctx)
    coins = refresh_copper_coins(state)
    if coins is None:
        state.copper_coins = 0
        coins = 0
        logger.warning("pick_shop 铜币识别失败，按 0 处理")
    logger.info("pick_shop 铜币=%s", coins)

    candidates: list[tuple[str, str]] = []
    if coins >= 30:
        candidates.append((BA_QING_STORE, "ba_qing_store"))
    candidates.extend(
        [
            (POCKET_EVENT, "pocket_event"),
            (REST, "rest"),
        ]
    )

    for path, outcome in candidates:
        c = shot.center(path)
        if c:
            Mouse().move(*c).click(clicks=2).sleep(0.2).perform()
            logger.info("pick_shop 选中 %s", outcome)
            if outcome == "ba_qing_store":
                time.sleep(0.6)
                shot2 = snap({BA_QING_STORE}, region=CHOICE_REGION)
                if shot2.found(BA_QING_STORE):
                    ctx.goto("qldq.battle_hub.pick_shop.verify_ba_qing")
                    return Result.success()
                ctx.goto("qldq.ba_qing_store.click_token_slot")
                return Result.success()
            ctx.goto(f"qldq.{outcome}")
            return Result.success()
    return Result.fail("商店选项均未识别")


def verify_ba_qing(ctx) -> Result:
    time.sleep(0.4)
    shot = snap({BA_QING_STORE}, region=CHOICE_REGION)
    if shot.found(BA_QING_STORE):
        return Result.fail("巴清图标仍在")
    ctx.goto("qldq.ba_qing_store.click_token_slot")
    return Result.success()
