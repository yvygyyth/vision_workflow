"""巴清商店 mod。"""

from __future__ import annotations

import logging
import time

from vision_bot.actions import click, do, move
from vision_bot.apps.ming_jiang_sha.actions import click_confirm
from vision_bot.apps.ming_jiang_sha.paths import QLDQ
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.utils.priority import TOKEN_PRIORITY
from vision_bot.core.input import press_key
from vision_bot.core.vision import grab_region, image_to_text
from vision_bot.runtime.relocate import RelocateRule
from vision_bot.runtime.result import Result
from vision_bot.vision import find, snap

logger = logging.getLogger(__name__)

GO_BACK = f"{QLDQ}/ba_qing_store/go_back.png"
CONFIRM = f"{QLDQ}/ba_qing_store/confirm.png"
_NO_BUY = f"{QLDQ}/ba_qing_store/no_buy.png"

TOKEN_TITLE_REGIONS: tuple[tuple[int, int, int, int], ...] = (
    (1276, 300, 280, 50),
    (1730, 300, 280, 50),
    (2186, 300, 280, 50),
)


relocate: list[RelocateRule] = [
    RelocateRule(
        when=lambda ctx: snap(GO_BACK).ok,
        then="qldq.ba_qing_store.click_token_slot",
    ),
]


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


def click_token_slot(ctx) -> Result:
    result = do(move().image(f"{QLDQ}/ba_qing_store/token_slot.png"), click())()
    if result.ok:
        return Result.success(then="qldq.ba_qing_store.slot_confirm")
    return Result.success(then="qldq.ba_qing_store.choose_token")


def slot_confirm(ctx) -> Result:
    if click_confirm().ok:
        return Result.success(then="qldq.ba_qing_store.choose_token")
    return Result.success(then="qldq.ba_qing_store.slot_no_buy")


def slot_no_buy(ctx) -> Result:
    return _close_no_buy(ctx, on_absent="qldq.ba_qing_store.choose_token")


def choose_token(ctx) -> Result:
    """OCR 三槽信物名，按 TOKEN_PRIORITY 点击；没有想要的则跳过购买。"""
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
        logger.info("choose_token → skip (%s)", "；".join(lines))
        return Result.success(then="qldq.ba_qing_store.go_back")

    name = next(
        (n for n in TOKEN_PRIORITY if n and n in (titles[slot] or "")),
        (titles[slot] or "").strip() or f"槽{slot + 1}",
    )
    left, top, width, height = TOKEN_TITLE_REGIONS[slot]
    cx = left + width // 2
    cy = top + height // 2
    logger.info("【巴清信物】槽位%s → %s 点击 (%s,%s)", slot + 1, name, cx, cy)
    do(move().to(cx, cy), click())()
    return Result.success(then="qldq.ba_qing_store.token_confirm")


def token_confirm(ctx) -> Result:
    if click_confirm().ok:
        return Result.success(then="qldq.ba_qing_store.go_back")
    return Result.success(then="qldq.ba_qing_store.token_no_buy")


def token_no_buy(ctx) -> Result:
    return _close_no_buy(ctx, on_absent="qldq.ba_qing_store.go_back")


def _close_no_buy(ctx, *, on_absent: str) -> Result:
    hit = find(_NO_BUY, timeout=1.2, threshold=0.8)
    if not hit.ok:
        logger.info("close_no_buy → 无弹窗，继续 %s", on_absent)
        return Result.success(then=on_absent)
    logger.info("close_no_buy → Esc 关闭 no_buy")
    press_key("esc")
    time.sleep(0.3)
    return Result.success(then="qldq.ba_qing_store.go_back")


def go_back(ctx) -> Result:
    do(move().image(GO_BACK).match(timeout=2.0), click())()
    time.sleep(0.4)
    return Result.success(then="qldq.ba_qing_store.confirm")


def confirm(ctx) -> Result:
    """点离店确认；点完即回三选一（不再 ensure 空转重试）。"""
    if not snap(GO_BACK).ok:
        logger.info("confirm → 已不在店内")
        return Result.success(then="qldq.battle_hub")

    r = do(move().image(CONFIRM).match(timeout=1.0), click())()
    if r.ok:
        logger.info("confirm → 已点确认，回三选一")
        return Result.success(then="qldq.battle_hub")

    # 确认按钮找不到：若返回键也没了，说明已经出去了
    if not snap(GO_BACK).ok:
        logger.info("confirm → 无确认且无返回，视为已离店")
        return Result.success(then="qldq.battle_hub")
    return Result.fail(r.message or "离店确认未找到")
