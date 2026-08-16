"""千里单骑 · 巴清商店动作。"""

from __future__ import annotations

import logging

from vision_workflow.apps.ming_jiang_sha.common.paths import DATA_ROOT
from vision_workflow.apps.ming_jiang_sha.parts.qian_li_dan_qi.utils import (
    TOKEN_PRIORITY,
    get_battle_state,
)
from vision_workflow.events import click, do, move
from vision_workflow.module import EventFn, ModuleContext
from vision_workflow.status import FULFILLED, OutcomeKey
from vision_workflow.vision import grab_region, image_to_text

logger = logging.getLogger(__name__)

_DIR = f"{DATA_ROOT}/qian_li_dan_qi/ba_qing_store"

# 店内信物标题区（相对模板基准；grab_region / move.to 会 fit）
TOKEN_TITLE_REGIONS: tuple[tuple[int, int, int, int], ...] = (
    (1276, 300, 280, 50),
    (1730, 300, 280, 50),
    (2186, 300, 280, 50),
)

click_token_slot: EventFn = do(move().image(f"{_DIR}/token_slot.png"), click())
click_go_back: EventFn = do(move().image(f"{_DIR}/go_back.png"), click())
click_confirm: EventFn = do(move().image(f"{_DIR}/confirm.png"), click())


def pick_token_slot(titles: list[str], priority: list[str] | None = None) -> int | None:
    """按 TOKEN_PRIORITY 顺序，返回本屏第一个命中的槽位下标；都没有则 None。"""
    table = priority if priority is not None else TOKEN_PRIORITY
    cleaned = [(i, (t or "").strip()) for i, t in enumerate(titles)]
    for name in table:
        if not name:
            continue
        for i, text in cleaned:
            if name in text:
                return i
    return None


def choose_token(m: ModuleContext) -> OutcomeKey:
    """OCR 三槽信物名，按 TOKEN_PRIORITY 点击；没有想要的则 skip。"""
    titles: list[str] = []
    lines: list[str] = []
    for i, region in enumerate(TOKEN_TITLE_REGIONS, start=1):
        text = image_to_text(grab_region(region))
        titles.append(text)
        shown = text if text else "(空)"
        lines.append(f"{i}:{shown}")
        logger.info("【巴清信物OCR】槽位%s → %s", i, shown)

    slot = pick_token_slot(titles)
    if slot is None:
        m.reason = f"{'；'.join(lines)} → 无匹配信物，跳过购买"
        logger.info("choose_token → skip")
        return "skip"

    name = next(
        (n for n in TOKEN_PRIORITY if n and n in (titles[slot] or "")),
        titles[slot].strip() or f"槽{slot + 1}",
    )
    left, top, width, height = TOKEN_TITLE_REGIONS[slot]
    cx = left + width // 2
    cy = top + height // 2
    logger.info("【巴清信物】槽位%s → %s 点击 (%s,%s)", slot + 1, name, cx, cy)
    m.reason = f"{'；'.join(lines)} → 选{slot + 1}:{name}"
    m.value = {"titles": titles, "slot": slot, "token": name}

    key = do(move().to(cx, cy), click())(m)
    if key == FULFILLED:
        get_battle_state(m.ctx).critical_tokens.add(name)
    return key if key is not None else FULFILLED
