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
from vision_bot.perception.signal import Signal
from vision_bot.perception.snapshot import capture
from vision_bot.runtime.context import RunContext
from vision_bot.runtime.result import Result
from vision_bot.vision import find

logger = logging.getLogger(__name__)

_DIR = f"{QLDQ}/ba_qing_store"
_NO_BUY = f"{_DIR}/no_buy.png"

SIGNALS: dict[str, Signal] = {
    "shop.go_back": Signal(template=f"{_DIR}/go_back.png"),
    "shop.confirm": Signal(template=f"{_DIR}/confirm.png"),
    "shop.no_buy": Signal(template=f"{_DIR}/no_buy.png"),
    "shop.token_slot": Signal(template=f"{_DIR}/token_slot.png"),
}

TOKEN_TITLE_REGIONS: tuple[tuple[int, int, int, int], ...] = (
    (1276, 300, 280, 50),
    (1730, 300, 280, 50),
    (2186, 300, 280, 50),
)

_EXIT_CONFIRM_TRIES = "ba_qing_exit_confirm_tries"
_EXIT_CONFIRM_MAX = 3


def relocate(ctx: RunContext) -> str | None:
    snap = capture(ctx.registry, ctx.base_dir, {"shop.go_back"})
    if snap.found("shop.go_back"):
        return "qldq.ba_qing_store.click_token_slot"
    return None


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
    result = do(move().image(f"{_DIR}/token_slot.png"), click())()
    if result.ok:
        ctx.goto("qldq.ba_qing_store.slot_confirm")
    else:
        ctx.goto("qldq.ba_qing_store.choose_token")
    return Result.success()


def slot_confirm(ctx) -> Result:
    if click_confirm().ok:
        ctx.goto("qldq.ba_qing_store.choose_token")
    else:
        ctx.goto("qldq.ba_qing_store.slot_no_buy")
    return Result.success()


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
        ctx.goto("qldq.ba_qing_store.go_back")
        return Result.success()

    name = next(
        (n for n in TOKEN_PRIORITY if n and n in (titles[slot] or "")),
        (titles[slot] or "").strip() or f"槽{slot + 1}",
    )
    left, top, width, height = TOKEN_TITLE_REGIONS[slot]
    cx = left + width // 2
    cy = top + height // 2
    logger.info("【巴清信物】槽位%s → %s 点击 (%s,%s)", slot + 1, name, cx, cy)
    do(move().to(cx, cy), click())()
    ctx.goto("qldq.ba_qing_store.token_confirm")
    return Result.success()


def token_confirm(ctx) -> Result:
    if click_confirm().ok:
        ctx.goto("qldq.ba_qing_store.go_back")
    else:
        ctx.goto("qldq.ba_qing_store.token_no_buy")
    return Result.success()


def token_no_buy(ctx) -> Result:
    return _close_no_buy(ctx, on_absent="qldq.ba_qing_store.go_back")


def _close_no_buy(ctx, *, on_absent: str) -> Result:
    hit = find(_NO_BUY, timeout=1.2, threshold=0.8)
    if not hit.ok:
        logger.info("close_no_buy → 无弹窗，继续 %s", on_absent)
        ctx.goto(on_absent)
        return Result.success()
    logger.info("close_no_buy → Esc 关闭 no_buy")
    press_key("esc")
    time.sleep(0.3)
    ctx.goto("qldq.ba_qing_store.go_back")
    return Result.success()


def go_back(ctx) -> Result:
    do(move().image(f"{_DIR}/go_back.png"), click())()
    time.sleep(0.6)
    ctx.goto("qldq.ba_qing_store.confirm")
    return Result.success()


def confirm(ctx) -> Result:
    do(move().image(f"{_DIR}/confirm.png"), click())()
    ctx.goto("qldq.ba_qing_store.ensure_left")
    return Result.success()


def ensure_left(ctx) -> Result:
    time.sleep(0.6)
    snap = ctx.snap({"shop.go_back"})
    if snap.found("shop.go_back"):
        tries = int(ctx.vars.get(_EXIT_CONFIRM_TRIES, 0)) + 1
        ctx.vars[_EXIT_CONFIRM_TRIES] = tries
        if tries > _EXIT_CONFIRM_MAX:
            logger.info("ensure_left → 确认重试超限，结束离店")
            ctx.vars.pop(_EXIT_CONFIRM_TRIES, None)
            ctx.goto("qldq.battle_hub")
            return Result.success()
        logger.info("ensure_left → still_here (%s/%s)", tries, _EXIT_CONFIRM_MAX)
        ctx.goto("qldq.ba_qing_store.confirm")
        return Result.success()
    logger.info("ensure_left → left")
    ctx.vars.pop(_EXIT_CONFIRM_TRIES, None)
    ctx.goto("qldq.battle_hub")
    return Result.success()
