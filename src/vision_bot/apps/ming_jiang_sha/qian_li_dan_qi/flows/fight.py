"""战斗 mod。"""

from __future__ import annotations

import logging
import time

from vision_bot.actions import click, do, move
from vision_bot.apps.ming_jiang_sha.paths import QLDQ
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.signals import FIGHT_DETECT
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.state import get_battle_state
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.utils.rewards import (
    GeneralPriority,
    RewardKind,
    parse_general_name,
    pick_reward_kind,
    pick_reward_slot,
    resolve_general_priority,
)
from vision_bot.core.input import Mouse
from vision_bot.core.vision import grab_region, image_to_text
from vision_bot.events import click_match
from vision_bot.perception.snapshot import ScreenSnapshot, capture
from vision_bot.runtime.context import RunContext
from vision_bot.runtime.result import Result
from vision_bot.vision import find

logger = logging.getLogger(__name__)

_AUTO = f"{QLDQ}/fight/auto.png"
_CHALLENGE_END = f"{QLDQ}/fight/challenge_end.png"
_NEXT_STEP = f"{QLDQ}/fight/next_step.png"
_CONFIRM = "data/ming_jiang_sha/common/confirm.png"

PENDING_GENERAL_KEY = "pending_reward_general"
PENDING_TITLES_KEY = "pending_reward_titles"

REWARD_TITLE_REGIONS: tuple[tuple[int, int, int, int], ...] = (
    (360, 1050, 290, 50),
    (1140, 1050, 290, 50),
    (1910, 1050, 290, 50),
)

REWARD_KIND_SIGNALS: dict[RewardKind, str] = {
    RewardKind.TOKEN: "fight.token",
    RewardKind.JOINT: "fight.joint",
    RewardKind.CARD: "fight.card",
    RewardKind.HELP: "fight.help",
    RewardKind.BUFF: "fight.buff",
}


def detect(snap: ScreenSnapshot, ctx: RunContext | None = None) -> str | None:
    if snap.found("fight.cancel"):
        return "qldq.fight.click_cancel"
    if snap.found("fight.setting"):
        return "qldq.fight.click_setting"
    if snap.found("fight.challenge_end"):
        return "qldq.fight.wait_end"
    if snap.found("fight.next_step"):
        return "qldq.fight.next_step"
    if ctx is not None and any(
        snap.found(signal) for signal in REWARD_KIND_SIGNALS.values()
    ):
        return "qldq.fight.choose_reward_kind"
    return "qldq.fight.click_cancel"


def relocate(ctx: RunContext) -> str | None:
    snap = capture(ctx.registry, ctx.base_dir, FIGHT_DETECT)
    return detect(snap, ctx)


def move_aside(ctx) -> Result:
    do(move().to(80, 80).raw())()
    return Result.success()


def click_cancel(ctx) -> Result:
    snap = ctx.snap({"fight.cancel"})
    c = snap.center("fight.cancel")
    if c:
        Mouse().move(*c).click().sleep(0.2).perform()
        return Result.success()
    return Result.fail("无 cancel")


def click_setting(ctx) -> Result:
    snap = ctx.snap({"fight.setting"})
    c = snap.center("fight.setting")
    if c:
        Mouse().move(*c).click().sleep(0.5).perform()
        return Result.success()
    return Result.fail("无 setting")


def click_auto(ctx) -> Result:
    result = find(_AUTO, timeout=1.0)
    if not result.ok:
        return Result.fail("无 auto")
    return click_match(result.value, pause=0.2)


def wait_end(ctx) -> Result:
    result = find(_CHALLENGE_END, timeout=1200, interval=5)
    if not result.ok:
        return Result.fail("挑战未结束")
    return click_match(result.value, pause=0.2)


def next_step(ctx) -> Result:
    for _ in range(5):
        result = find(_NEXT_STEP, timeout=1.2)
        if not result.ok or not result.value.center:
            break
        click_match(result.value, pause=0.4)
    ctx.goto("qldq.fight.check_run_end")
    return Result.success()


def check_run_end(ctx) -> Result:
    if find(_CONFIRM, timeout=1.0, threshold=0.8).ok:
        logger.info("check_run_end → run_ended")
        ctx.goto("qldq.run_ended.confirm")
        return Result.success()
    ctx.goto("qldq.fight.after_settle")
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
        ctx.goto("qldq.fight.choose_reward_title")
        return Result.success()
    logger.info("after_settle → 无赠礼 UI，回三选一")
    ctx.goto("qldq.battle_hub")
    return Result.success()


def choose_reward_title(ctx) -> Result:
    cached = ctx.vars.pop(PENDING_TITLES_KEY, None)
    titles = cached if isinstance(cached, list) else _ocr_reward_titles()
    if not titles_look_like_gift(titles):
        logger.info("choose_reward_title → no_gift")
        ctx.goto("qldq.battle_hub")
        return Result.success()

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
    ctx.goto("qldq.fight.choose_reward_kind")
    return Result.success()


def _scan_reward_kinds(ctx) -> dict[RewardKind, tuple[int, int]]:
    snap = ctx.snap(set(REWARD_KIND_SIGNALS.values()))
    available: dict[RewardKind, tuple[int, int]] = {}
    for kind, signal in REWARD_KIND_SIGNALS.items():
        c = snap.center(signal)
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
        ctx.goto("qldq.battle_hub")
        return Result.success()

    kind = pick_reward_kind(available.keys(), entry, state)
    if kind is None:
        logger.warning("choose_reward_kind → 无可选项")
        ctx.vars.pop(PENDING_GENERAL_KEY, None)
        ctx.goto("qldq.battle_hub")
        return Result.success()

    cx, cy = available[kind]
    general = entry.name if entry else "?"
    logger.info("【赠礼类别】%s → %s 点击 (%s,%s)", general, kind.value, cx, cy)
    do(move().to(cx, cy).raw(), click())()
    if entry is not None and entry.name:
        state.mark_general_reward(entry.name, kind)
        logger.info("【背包】%s ← %s", entry.name, kind.value)
    ctx.vars.pop(PENDING_GENERAL_KEY, None)
    ctx.goto("qldq.battle_hub")
    return Result.success()
