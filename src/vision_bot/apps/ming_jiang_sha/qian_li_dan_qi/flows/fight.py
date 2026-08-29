"""战斗外壳：call 纯战斗后，按有无赠礼结算。"""

from __future__ import annotations

import logging
import time

from vision_bot.actions import click, do, move
from vision_bot.apps.ming_jiang_sha.paths import QLDQ
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.state import get_battle_state
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.utils.rewards import (
    GeneralPriority,
    RewardKind,
    parse_general_name,
    pick_reward_kind,
    pick_reward_slot,
    resolve_general_priority,
)
from vision_bot.apps.ming_jiang_sha.tools.battle import RUN_ENDED_FLAG
from vision_bot.core.vision import grab_region, image_to_text
from vision_bot.runtime.result import Result
from vision_bot.vision import snap

logger = logging.getLogger(__name__)

TOKEN = f"{QLDQ}/fight/token.png"
JOINT = f"{QLDQ}/fight/joint.png"
CARD = f"{QLDQ}/fight/card.png"
HELP = f"{QLDQ}/fight/help.png"
BUFF = f"{QLDQ}/fight/buff.png"

PENDING_GENERAL_KEY = "pending_reward_general"
PENDING_TITLES_KEY = "pending_reward_titles"

REWARD_TITLE_REGIONS: tuple[tuple[int, int, int, int], ...] = (
    (360, 1050, 290, 50),
    (1140, 1050, 290, 50),
    (1910, 1050, 290, 50),
)

REWARD_KIND_IMGS: dict[RewardKind, str] = {
    RewardKind.TOKEN: TOKEN,
    RewardKind.JOINT: JOINT,
    RewardKind.CARD: CARD,
    RewardKind.HELP: HELP,
    RewardKind.BUFF: BUFF,
}


def run_battle(ctx) -> Result:
    """同步执行名将杀共用纯战斗；本轮结束则跳 run_ended，否则进入结算。"""
    return _after_mjs_battle(ctx, then=None)


def run_battle_no_gift(ctx) -> Result:
    """无赠礼战斗（锦囊/十常侍等）：call 纯战斗后回三选一。"""
    return _after_mjs_battle(ctx, then="qldq.battle_hub")


def _after_mjs_battle(ctx, *, then: str | None) -> Result:
    r = ctx.call("mjs.battle")
    if not r.ok:
        return r
    if ctx.vars.pop(RUN_ENDED_FLAG, None):
        return Result.success(then="qldq.run_ended.confirm")
    if then:
        logger.info("run_battle_no_gift → 回三选一")
        return Result.success(then=then)
    return Result.success()


def _ocr_reward_titles() -> list[str]:
    titles: list[str] = []
    for i, region in enumerate(REWARD_TITLE_REGIONS, start=1):
        text = image_to_text(grab_region(region))
        titles.append(text)
        logger.info("【赠礼OCR】槽位%s → %s", i, text if text else "(空)")
    return titles


def titles_look_like_gift(titles: list[str]) -> bool:
    for text in titles:
        if parse_general_name(text):
            return True
        raw = (text or "").strip()
        if "赠礼" in raw or "贈禮" in raw:
            return True
    return False


def after_settle(ctx) -> Result:
    titles = _ocr_reward_titles()
    if titles_look_like_gift(titles):
        ctx.vars[PENDING_TITLES_KEY] = titles
        logger.info("after_settle → has_gift")
        return Result.success(then="qldq.fight.choose_reward_title")
    logger.info("after_settle → 无赠礼 UI，回三选一")
    return Result.success(then="qldq.battle_hub")


def choose_reward_title(ctx) -> Result:
    cached = ctx.vars.pop(PENDING_TITLES_KEY, None)
    titles = cached if isinstance(cached, list) else _ocr_reward_titles()
    if not titles_look_like_gift(titles):
        logger.info("choose_reward_title → no_gift")
        return Result.success(then="qldq.battle_hub")

    state = get_battle_state(ctx)
    slot = pick_reward_slot(titles, state)
    picked = parse_general_name(titles[slot]) or f"槽{slot + 1}"
    entry = resolve_general_priority(picked)
    ctx.vars[PENDING_GENERAL_KEY] = entry

    left, top, width, height = REWARD_TITLE_REGIONS[slot]
    cx = left + width // 2
    cy = top + height // 2
    logger.info(
        "【赠礼选择】槽位%s → %s key=%s 点击 (%s,%s)",
        slot + 1,
        entry.name,
        [k.value for k in entry.key_rewards],
        cx,
        cy,
    )
    do(move().to(cx, cy), click())()
    return Result.success(then="qldq.fight.choose_reward_kind")


def _scan_reward_kinds(ctx) -> dict[RewardKind, tuple[int, int]]:
    shot = snap(set(REWARD_KIND_IMGS.values()))
    available: dict[RewardKind, tuple[int, int]] = {}
    for kind, path in REWARD_KIND_IMGS.items():
        c = shot.center(path)
        if c is not None:
            available[kind] = c
            logger.info("【赠礼选项】可用 %s @ %s", kind.value, c)
    return available


def choose_reward_kind(ctx) -> Result:
    state = get_battle_state(ctx)
    entry = ctx.vars.get(PENDING_GENERAL_KEY)
    if not isinstance(entry, GeneralPriority):
        entry = None

    time.sleep(0.6)
    available = _scan_reward_kinds(ctx)
    if not available:
        time.sleep(0.5)
        available = _scan_reward_kinds(ctx)

    if not available:
        logger.warning("choose_reward_kind → no_kind")
        ctx.vars.pop(PENDING_GENERAL_KEY, None)
        return Result.success(then="qldq.battle_hub")

    kind = pick_reward_kind(available.keys(), entry, state)
    if kind is None:
        logger.warning("choose_reward_kind → 无可选项")
        ctx.vars.pop(PENDING_GENERAL_KEY, None)
        return Result.success(then="qldq.battle_hub")

    cx, cy = available[kind]
    general = entry.name if entry else "?"
    logger.info("【赠礼类别】%s → %s 点击 (%s,%s)", general, kind.value, cx, cy)
    do(move().to(cx, cy).raw(), click())()
    if entry is not None and entry.name:
        state.mark_general_reward(entry.name, kind)
        logger.info("【背包】%s ← %s", entry.name, kind.value)
    ctx.vars.pop(PENDING_GENERAL_KEY, None)
    return Result.success(then="qldq.battle_hub")
