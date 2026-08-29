"""商店三选一 mod。"""

from __future__ import annotations

import logging
import time

from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.state import get_battle_state
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.utils.bag import refresh_copper_coins
from vision_bot.core.input import Mouse
from vision_bot.perception.snapshot import ScreenSnapshot, snap
from vision_bot.runtime.context import RunContext
from vision_bot.runtime.result import Result

logger = logging.getLogger(__name__)

DETECT: set[str] = {
    "choice.ba_qing_store",
    "choice.pocket_event",
    "choice.rest",
    "choice.lv_bu_wei_store",
}


def detect(shot: ScreenSnapshot, ctx: RunContext | None = None) -> str | None:
    if any(
        shot.found(k)
        for k in ("choice.ba_qing_store", "choice.pocket_event", "choice.rest", "choice.lv_bu_wei_store")
    ):
        return "qldq.battle_hub.pick_shop.choose"
    return None


def relocate(ctx: RunContext) -> str | None:
    shot = snap(DETECT)
    return detect(shot, ctx)


def choose(ctx) -> Result:
    shot = snap(DETECT)
    state = get_battle_state(ctx)
    coins = refresh_copper_coins(state)
    if coins is None:
        state.copper_coins = 0
        coins = 0
        logger.warning("pick_shop 铜币识别失败，按 0 处理")
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
        c = shot.center(key)
        if c:
            Mouse().move(*c).click(clicks=2).sleep(0.2).perform()
            logger.info("pick_shop 选中 %s", outcome)
            if outcome == "ba_qing_store":
                time.sleep(0.6)
                shot2 = snap({"choice.ba_qing_store"})
                if shot2.found("choice.ba_qing_store"):
                    ctx.goto("qldq.battle_hub.pick_shop.verify_ba_qing")
                    return Result.success()
                ctx.goto("qldq.ba_qing_store.click_token_slot")
                return Result.success()
            ctx.goto(f"qldq.{outcome}")
            return Result.success()
    return Result.fail("商店选项均未识别")


def verify_ba_qing(ctx) -> Result:
    time.sleep(0.4)
    shot = snap({"choice.ba_qing_store"})
    if shot.found("choice.ba_qing_store"):
        return Result.fail("巴清图标仍在")
    ctx.goto("qldq.ba_qing_store.click_token_slot")
    return Result.success()
