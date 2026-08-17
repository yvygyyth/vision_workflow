"""千里单骑 · 开打动作。"""

from __future__ import annotations

import logging

from vision_workflow.apps.ming_jiang_sha.common.paths import COMMON_DIR, DATA_ROOT
from vision_workflow.apps.ming_jiang_sha.parts.qian_li_dan_qi.fight.params import (
    PARAM_GIFT,
    FightGift,
)
from vision_workflow.apps.ming_jiang_sha.parts.qian_li_dan_qi.run_ended import RUN_ENDED
from vision_workflow.apps.ming_jiang_sha.parts.qian_li_dan_qi.utils import (
    GeneralPriority,
    RewardKind,
    get_battle_state,
    parse_general_name,
    pick_reward_kind,
    pick_reward_slot,
    resolve_general_priority,
)
from vision_workflow.events import click, do, move
from vision_workflow.module import EventFn, ModuleContext
from vision_workflow.status import FULFILLED, REJECTED, OutcomeKey
from vision_workflow.vision import grab_region, image_to_text

logger = logging.getLogger(__name__)

_DIR = f"{DATA_ROOT}/qian_li_dan_qi/fight"
_CONFIRM = f"{COMMON_DIR}/confirm.png"

CANCEL_IMAGE = f"{_DIR}/cancel.png"

# FlowContext.vars：选择武将后暂存，供下一步选类别
PENDING_GENERAL_KEY = "pending_reward_general"
PENDING_TITLES_KEY = "pending_reward_titles"

# 结算三选一标题区（相对模板基准；grab_region / move.to 会 fit）
REWARD_TITLE_REGIONS: tuple[tuple[int, int, int, int], ...] = (
    (360, 1050, 290, 50),
    (1140, 1050, 290, 50),
    (1910, 1050, 290, 50),
)

# 点开武将赠礼后的具体选项模板
REWARD_KIND_TEMPLATES: dict[RewardKind, str] = {
    RewardKind.TOKEN: f"{_DIR}/token.png",
    RewardKind.JOINT: f"{_DIR}/joint.png",
    RewardKind.CARD: f"{_DIR}/card.png",
    RewardKind.HELP: f"{_DIR}/help.png",
    RewardKind.BUFF: f"{_DIR}/buff.png",
}

click_cancel: EventFn = do(move().image(CANCEL_IMAGE), click())
# 勿用 (0,0)：PyAutoGUI 角落 FailSafe 会导致后续操作抛异常
move_aside: EventFn = do(move().to(80, 80).raw())
click_setting: EventFn = do(move().image(f"{_DIR}/setting.png"), click())
click_auto: EventFn = do(move().image(f"{_DIR}/auto.png"), click())
click_challenge_end: EventFn = do(
    move().image(f"{_DIR}/challenge_end.png").match(timeout=600, interval=5),
    click(),
)
click_next_step: EventFn = do(move().image(f"{_DIR}/next_step.png"), click())


def check_run_end(m: ModuleContext) -> OutcomeKey:
    """下一步后：仍有公共确认框 → 本轮结束；否则继续结算分支。"""
    if m.find(_CONFIRM, timeout=1.0, threshold=0.8).found:
        m.reason = "下一步后仍有确认框，本轮结束"
        logger.info("check_run_end → run_ended")
        return RUN_ENDED
    logger.info("check_run_end → continue settle")
    return FULFILLED


def cancel_visible(m: ModuleContext, *, timeout: float = 0.8) -> bool:
    """战斗「取消」按钮是否在画面上。"""
    return bool(m.find(CANCEL_IMAGE, timeout=timeout, threshold=0.8).found)


def _gift_param(m: ModuleContext) -> FightGift:
    raw = m.params.get(PARAM_GIFT, FightGift.WITH)
    if isinstance(raw, FightGift):
        return raw
    try:
        return FightGift(str(raw))
    except ValueError:
        logger.warning("未知 gift 入参 %r，按 WITH 处理", raw)
        return FightGift.WITH


def _ocr_reward_titles() -> list[str]:
    titles: list[str] = []
    for i, region in enumerate(REWARD_TITLE_REGIONS, start=1):
        text = image_to_text(grab_region(region))
        titles.append(text)
        logger.info("【赠礼OCR】槽位%s → %s", i, text if text else "(空)")
    return titles


def titles_look_like_gift(titles: list[str]) -> bool:
    """三槽里是否像赠礼界面（有武将名或「赠礼」字样）。"""
    for text in titles:
        if parse_general_name(text):
            return True
        raw = (text or "").strip()
        if "赠礼" in raw or "贈禮" in raw:
            return True
    return False


def after_settle_branch(m: ModuleContext) -> OutcomeKey:
    """结算后：无赠礼或识不到→fulfilled 回三选一；识到→选赠礼。"""
    if _gift_param(m) is FightGift.WITHOUT:
        m.reason = "无赠礼，回战斗选择"
        logger.info("after_settle_branch → fulfilled（无赠礼）")
        return FULFILLED

    titles = _ocr_reward_titles()
    if titles_look_like_gift(titles):
        m.vars[PENDING_TITLES_KEY] = titles
        m.reason = "识别到赠礼"
        logger.info("after_settle_branch → has_gift")
        return "has_gift"

    m.reason = "有赠礼模式但未识别到赠礼，回三选一判断"
    logger.info("after_settle_branch → fulfilled（无赠礼 UI）")
    return FULFILLED


def choose_reward_title(m: ModuleContext) -> OutcomeKey:
    """OCR 三槽标题，按优先表 + 背包选槽并点击；识不到则 no_gift。"""
    cached = m.vars.pop(PENDING_TITLES_KEY, None)
    titles = cached if isinstance(cached, list) else _ocr_reward_titles()
    if not titles_look_like_gift(titles):
        m.reason = "未识别到赠礼标题"
        logger.info("choose_reward_title → no_gift")
        return "no_gift"

    lines = [f"{i}:{(t if t else '(空)')}" for i, t in enumerate(titles, start=1)]
    state = get_battle_state(m.ctx)
    slot = pick_reward_slot(titles, state)
    picked = parse_general_name(titles[slot]) or f"槽{slot + 1}"
    entry = resolve_general_priority(picked)
    m.vars[PENDING_GENERAL_KEY] = entry

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
    m.reason = f"{'；'.join(lines)} → 选{slot + 1}:{entry.name}"
    m.value = {"titles": titles, "slot": slot, "general": entry}

    key = do(move().to(cx, cy), click())(m)
    return key if key is not None else FULFILLED


def choose_reward_kind(m: ModuleContext) -> OutcomeKey:
    """识图信物/并肩/武将牌/资助/驰援，按 ctx.vars 里的武将 + 背包点最高优先项。"""
    state = get_battle_state(m.ctx)
    entry = m.vars.get(PENDING_GENERAL_KEY)
    if not isinstance(entry, GeneralPriority):
        entry = None

    available: dict[RewardKind, tuple[int, int]] = {}
    for kind, path in REWARD_KIND_TEMPLATES.items():
        hit = m.find(path, timeout=0.0)
        if hit.found and hit.center is not None:
            available[kind] = hit.center
            logger.info(
                "【赠礼选项】可用 %s @ %s (%.2f)",
                kind.value,
                hit.center,
                hit.confidence,
            )

    if not available:
        m.reason = "未识别到信物/并肩作战/武将牌/资助/驰援"
        return REJECTED

    kind = pick_reward_kind(available.keys(), entry, state)
    if kind is None:
        m.reason = "无可选赠礼类别"
        return REJECTED

    cx, cy = available[kind]
    general = entry.name if entry else "?"
    logger.info("【赠礼类别】%s → %s 点击 (%s,%s)", general, kind.value, cx, cy)
    m.reason = f"{general} → {kind.value}"
    m.value = {"general": entry, "kind": kind, "available": list(available)}

    key = do(move().to(cx, cy).raw(), click())(m)
    if key == FULFILLED:
        if entry is not None and entry.name:
            state.mark_general_reward(entry.name, kind)
            logger.info("【背包】%s ← %s", entry.name, kind.value)
        m.vars.pop(PENDING_GENERAL_KEY, None)
    return key if key is not None else FULFILLED
