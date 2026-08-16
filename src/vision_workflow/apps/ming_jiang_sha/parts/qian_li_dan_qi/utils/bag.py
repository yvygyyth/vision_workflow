"""局内背包读数（铜币等 UI OCR）。"""

from __future__ import annotations

import logging
import re

from vision_workflow.apps.ming_jiang_sha.parts.qian_li_dan_qi.utils.state import (
    BattleState,
)
from vision_workflow.vision import grab_region, image_to_text

logger = logging.getLogger(__name__)

# 相对模板基准：(left, top, width, height)
COPPER_REGION: tuple[int, int, int, int] = (2250, 96, 110, 40)


def parse_copper_text(text: str) -> int | None:
    """从 OCR 文案解析铜币整数；失败返回 None。"""
    raw = (text or "").strip()
    if not raw:
        return None
    cleaned = (
        raw.replace(",", "")
        .replace("，", "")
        .replace(" ", "")
        .replace("O", "0")
        .replace("o", "0")
        .replace("l", "1")
        .replace("I", "1")
    )
    match = re.search(r"\d+", cleaned)
    if not match:
        return None
    return int(match.group(0))


def read_copper_coins(*, region_fit: bool = True) -> int | None:
    """截取铜币区域 OCR，返回数量；识别失败为 None。"""
    img = grab_region(COPPER_REGION, region_fit=region_fit)
    text = image_to_text(img)
    amount = parse_copper_text(text)
    logger.info("铜币OCR region=%s text=%r → %s", COPPER_REGION, text, amount)
    return amount


def refresh_copper_coins(state: BattleState, *, region_fit: bool = True) -> int | None:
    """OCR 铜币并写回 ``BattleState.copper_coins``；失败不改原值。"""
    amount = read_copper_coins(region_fit=region_fit)
    if amount is None:
        return None
    state.copper_coins = amount
    return amount
