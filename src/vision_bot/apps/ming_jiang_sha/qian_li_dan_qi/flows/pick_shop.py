"""商店三选一 mod。"""

from __future__ import annotations

import logging

from vision_bot.actions import click, do, move
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.flows.battle_hub import (
    BA_QING_STORE,
    CHOICE_REGION,
    LV_BU_WEI_STORE,
    POCKET_EVENT,
    REST,
)
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.state import get_battle_state
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.utils.bag import refresh_copper_coins
from vision_bot.runtime.context import RunContext
from vision_bot.runtime.relocate import RelocateRule
from vision_bot.runtime.result import Result
from vision_bot.vision import snap

logger = logging.getLogger(__name__)

DETECT: set[str] = {BA_QING_STORE, POCKET_EVENT, REST, LV_BU_WEI_STORE}

# (模板, 流程名, 最低铜币)
_PRIORITY = (
    (BA_QING_STORE, "ba_qing_store", 30),
    (POCKET_EVENT, "pocket_event", 0),
    (REST, "rest", 0),
)


def _has_shop_choice(ctx: RunContext) -> bool:
    return snap(DETECT, region=CHOICE_REGION).race


relocate: list[RelocateRule] = [
    RelocateRule(when=_has_shop_choice, then="qldq.battle_hub.pick_shop.choose"),
]


def choose(ctx) -> Result:
    coins = refresh_copper_coins(get_battle_state(ctx))
    if coins is None:
        coins = 0
        logger.warning("pick_shop 铜币识别失败，按 0 处理")
    logger.info("pick_shop 铜币=%s", coins)

    for path, outcome, need in _PRIORITY:
        if coins < need:
            continue
        r = do(
            move().image(path).match(region=CHOICE_REGION, timeout=0),
            click().pause(0.5),
            click(),
        )()
        if not r.ok:
            continue
        logger.info("pick_shop 进入 %s", outcome)
        ctx.goto(f"qldq.{outcome}")
        return Result.success()
    return Result.fail("商店选项均未识别")
