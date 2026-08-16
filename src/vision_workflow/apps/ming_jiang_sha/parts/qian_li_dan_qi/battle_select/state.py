"""千里单骑局内状态：挂在 FlowContext.vars。

由 Workflow.lifecycle 绑定 / 清理（跨 battle_select / fight 保留）。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from vision_workflow.flow.context import FlowContext

VARS_KEY = "qian_li_dan_qi_battle"


@dataclass
class BattleState:
    """一局战斗内的背包 / 增益 / 铜币。"""

    critical_tokens: set[str] = field(default_factory=set)
    buffs: set[str] = field(default_factory=set)
    copper_coins: int = 0

    def has_critical_token(self, name: str = "关键信物") -> bool:
        return name in self.critical_tokens

    def has_buff(self, name: str = "驰援") -> bool:
        return name in self.buffs


def bind_battle_state(ctx: FlowContext) -> BattleState:
    """Workflow.on_enter：新建一局状态。"""
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
