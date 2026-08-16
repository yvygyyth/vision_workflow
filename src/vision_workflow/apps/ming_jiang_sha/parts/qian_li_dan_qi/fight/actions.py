"""千里单骑 · 开打动作。"""

from __future__ import annotations

from vision_workflow.apps.ming_jiang_sha.common.paths import DATA_ROOT
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

_DIR = f"{DATA_ROOT}/qian_li_dan_qi/fight"

# FlowContext.vars：选择武将后暂存，供下一步选类别
PENDING_GENERAL_KEY = "pending_reward_general"

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

click_cancel: EventFn = do(move().image(f"{_DIR}/cancel.png"), click())
# 勿用 (0,0)：PyAutoGUI 角落 FailSafe 会导致后续操作抛异常
move_aside: EventFn = do(move().to(80, 80).raw())
click_setting: EventFn = do(move().image(f"{_DIR}/setting.png"), click())
click_auto: EventFn = do(move().image(f"{_DIR}/auto.png"), click())
click_challenge_end: EventFn = do(
    move().image(f"{_DIR}/challenge_end.png").match(timeout=600, interval=5),
    click(),
)
click_next_step: EventFn = do(move().image(f"{_DIR}/next_step.png"), click())


def choose_reward_title(m: ModuleContext) -> OutcomeKey:
    """OCR 三槽标题，按优先表 + 背包选槽并点击；GeneralPriority 写入 ctx.vars。"""
    titles: list[str] = []
    lines: list[str] = []
    for i, region in enumerate(REWARD_TITLE_REGIONS, start=1):
        text = image_to_text(grab_region(region))
        titles.append(text)
        shown = text if text else "(空)"
        lines.append(f"{i}:{shown}")
        m.log("【赠礼OCR】槽位%s → %s", i, shown)

    state = get_battle_state(m.ctx)
    slot = pick_reward_slot(titles, state)
    picked = parse_general_name(titles[slot]) or f"槽{slot + 1}"
    entry = resolve_general_priority(picked)
    m.vars[PENDING_GENERAL_KEY] = entry

    left, top, width, height = REWARD_TITLE_REGIONS[slot]
    cx = left + width // 2
    cy = top + height // 2
    m.log(
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
            m.log("【赠礼选项】可用 %s @ %s (%.2f)", kind.value, hit.center, hit.confidence)

    if not available:
        m.reason = "未识别到信物/并肩作战/武将牌/资助/驰援"
        return REJECTED

    kind = pick_reward_kind(available.keys(), entry, state)
    if kind is None:
        m.reason = "无可选赠礼类别"
        return REJECTED

    cx, cy = available[kind]
    general = entry.name if entry else "?"
    m.log("【赠礼类别】%s → %s 点击 (%s,%s)", general, kind.value, cx, cy)
    m.reason = f"{general} → {kind.value}"
    m.value = {"general": entry, "kind": kind, "available": list(available)}

    key = do(move().to(cx, cy).raw(), click())(m)
    if key == FULFILLED:
        state.mark_reward(kind)
        if kind is RewardKind.TOKEN:
            state.critical_tokens.add("关键信物")
        elif kind is RewardKind.BUFF:
            state.buffs.add("驰援")
        elif kind is RewardKind.HELP:
            state.buffs.add("资助")
        m.vars.pop(PENDING_GENERAL_KEY, None)
    return key if key is not None else FULFILLED
