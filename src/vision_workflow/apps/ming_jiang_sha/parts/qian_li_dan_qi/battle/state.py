"""千里单骑战斗局内状态：挂在 FlowContext.vars，随 Flow.lifecycle.on_exit 清理。"""

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
    """lifecycle.on_enter：新建一局状态。"""
    state = BattleState()
    ctx.vars[VARS_KEY] = state
    return state


def get_battle_state(ctx: FlowContext) -> BattleState:
    """读取当前局状态；尚未 bind 时惰性创建。"""
    state = ctx.vars.get(VARS_KEY)
    if not isinstance(state, BattleState):
        return bind_battle_state(ctx)
    return state


def clear_battle_state(ctx: FlowContext) -> None:
    """lifecycle.on_exit：丢掉本局状态。"""
    ctx.vars.pop(VARS_KEY, None)
