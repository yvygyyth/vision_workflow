"""千里单骑局内状态：挂在 FlowContext.vars。

由 Workflow.lifecycle 绑定 / 清理（跨 battle_select / fight 保留）。
战斗赠礼按武将记录已拿到的奖励类别。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from vision_workflow.apps.ming_jiang_sha.parts.qian_li_dan_qi.utils.rewards import (
    RewardKind,
)
from vision_workflow.flow.context import FlowContext

VARS_KEY = "qian_li_dan_qi_battle"


@dataclass
class BattleState:
    """一局内：铜币 + 各武将已拿的赠礼类别。"""

    copper_coins: int = 0
    # 武将名 → 已拿到的奖励类别
    general_rewards: dict[str, set[RewardKind]] = field(default_factory=dict)

    def has_general_reward(self, name: str, kind: RewardKind) -> bool:
        return kind in self.general_rewards.get(name, set())

    def mark_general_reward(self, name: str, kind: RewardKind) -> None:
        self.general_rewards.setdefault(name, set()).add(kind)

    def has_reward(self, kind: RewardKind) -> bool:
        return any(kind in kinds for kinds in self.general_rewards.values())

    def mark_reward(self, kind: RewardKind) -> None:
        """无武将名时的兼容写入（记到空名下，仅测试用）。"""
        self.mark_general_reward("", kind)


def bind_battle_state(ctx: FlowContext) -> BattleState:
    """Workflow.on_enter / enter_battle.on_enter：新建一局状态。"""
    state = BattleState()
    ctx.vars[VARS_KEY] = state
    return state


def ensure_battle_state(ctx: FlowContext) -> BattleState:
    """已有则保留，没有再创建。"""
    state = ctx.vars.get(VARS_KEY)
    if isinstance(state, BattleState):
        return state
    return bind_battle_state(ctx)


def get_battle_state(ctx: FlowContext) -> BattleState:
    """读取当前局状态；尚未创建时惰性 ensure。"""
    return ensure_battle_state(ctx)


def clear_battle_state(ctx: FlowContext) -> None:
    """Workflow.on_exit：丢掉本局状态。"""
    ctx.vars.pop(VARS_KEY, None)
