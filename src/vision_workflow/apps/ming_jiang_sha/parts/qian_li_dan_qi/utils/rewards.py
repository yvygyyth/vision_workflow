"""赠礼优先表与选槽逻辑。

点「xx赠礼」只选武将槽；具体信物 / 资助 / 驰援等是点开之后的下一步。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol


class RewardKind(StrEnum):
    """赠礼内可选奖励类别。"""

    TOKEN = "信物"
    JOINT = "共同作战"
    HELP = "资助"
    BUFF = "驰援"
    CARD = "武将牌"


@dataclass(frozen=True)
class GeneralPriority:
    """优先表一行：武将名 + 关键奖励（越靠前越优先）。"""

    name: str
    key_rewards: tuple[RewardKind, ...]


class _RewardBag(Protocol):
    def has_reward(self, kind: RewardKind) -> bool: ...


def _priority_table() -> list[GeneralPriority]:
    # 延迟导入，避免与 priority 配置循环依赖
    from vision_workflow.apps.ming_jiang_sha.parts.qian_li_dan_qi.utils.priority import (
        PRIORITY,
    )

    return PRIORITY


def _fallback_kind_order() -> tuple[RewardKind, ...]:
    from vision_workflow.apps.ming_jiang_sha.parts.qian_li_dan_qi.utils.priority import (
        FALLBACK_KIND_ORDER,
    )

    return FALLBACK_KIND_ORDER


def _default_key_rewards() -> tuple[RewardKind, ...]:
    from vision_workflow.apps.ming_jiang_sha.parts.qian_li_dan_qi.utils.priority import (
        DEFAULT_KEY_REWARDS,
    )

    return DEFAULT_KEY_REWARDS


def parse_general_name(ocr_text: str) -> str:
    """从 OCR 文案取出武将名（去掉「赠礼」等后缀）。"""
    text = (ocr_text or "").strip()
    if not text or text == "(空)":
        return ""
    for suffix in ("赠礼", "贈禮"):
        if text.endswith(suffix):
            text = text[: -len(suffix)]
    return text.strip()


def _entry_by_name(name: str) -> GeneralPriority | None:
    if not name:
        return None
    for entry in _priority_table():
        if entry.name == name:
            return entry
    return None


def resolve_general_priority(name: str) -> GeneralPriority:
    """查优先表；不在表内则用 ``DEFAULT_KEY_REWARDS``。"""
    entry = _entry_by_name(name)
    if entry is not None:
        return entry
    return GeneralPriority(name=name or "未知", key_rewards=_default_key_rewards())


def _needed_key_rewards(entry: GeneralPriority, state: _RewardBag) -> list[RewardKind]:
    return [kind for kind in entry.key_rewards if not state.has_reward(kind)]


def _fallback_kind_rank(entry: GeneralPriority | None) -> int:
    """回退用：关键奖励里最靠前的类别秩；无关键奖励最差。"""
    order = _fallback_kind_order()
    if entry is None or not entry.key_rewards:
        return len(order)
    best = len(order)
    for kind in entry.key_rewards:
        try:
            best = min(best, order.index(kind))
        except ValueError:
            continue
    return best


def pick_reward_slot(
    titles: list[str] | tuple[str, ...],
    state: _RewardBag,
) -> int:
    """根据 OCR 标题与局内状态选出要点的槽位下标（0-based）。

    1. 按 PRIORITY 表顺序：本屏有该武将，且仍有未拿关键奖励 → 选他
    2. 否则回退：本屏选项按 FALLBACK_KIND_ORDER，同档靠左
    """
    names = [parse_general_name(t) for t in titles]
    if not names:
        return 0

    for entry in _priority_table():
        if entry.name not in names:
            continue
        if _needed_key_rewards(entry, state):
            return names.index(entry.name)

    best_slot = 0
    best_key = (_fallback_kind_rank(None), 0)
    for slot, name in enumerate(names):
        entry = _entry_by_name(name)
        if entry is None and name:
            entry = resolve_general_priority(name)
        key = (_fallback_kind_rank(entry), slot)
        if key < best_key:
            best_key = key
            best_slot = slot
    return best_slot


def pick_reward_kind(
    available: set[RewardKind] | list[RewardKind] | tuple[RewardKind, ...],
    entry: GeneralPriority | None,
    state: _RewardBag,
) -> RewardKind | None:
    """在本屏可选项里选出要拿的奖励类别。

    顺序：当前武将 ``key_rewards``（优先未拿到的）→ ``FALLBACK_KIND_ORDER``。
    """
    avail = set(available)
    if not avail:
        return None

    order: list[RewardKind] = []
    if entry is not None:
        order.extend(entry.key_rewards)
    for kind in _fallback_kind_order():
        if kind not in order:
            order.append(kind)

    for kind in order:
        if kind in avail and not state.has_reward(kind):
            return kind
    for kind in order:
        if kind in avail:
            return kind
    return None
