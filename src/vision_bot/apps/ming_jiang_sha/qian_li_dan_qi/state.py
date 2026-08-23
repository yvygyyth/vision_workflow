"""千里单骑 · 局内状态。"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class RewardKind(str, Enum):
    TOKEN = "token"
    JOINT = "joint"
    CARD = "card"
    HELP = "help"
    BUFF = "buff"


@dataclass
class BattleState:
    copper_coins: int = 0
    general_rewards: dict[str, set[RewardKind]] = field(default_factory=dict)

    def has_general_reward(self, name: str, kind: RewardKind) -> bool:
        return kind in self.general_rewards.get(name, set())

    def mark_general_reward(self, name: str, kind: RewardKind) -> None:
        self.general_rewards.setdefault(name, set()).add(kind)


VARS_BATTLE_STATE = "battle_state"


def bind_battle_state(ctx) -> BattleState:
    state = BattleState()
    ctx.vars[VARS_BATTLE_STATE] = state
    return state


def clear_battle_state(ctx) -> None:
    ctx.vars.pop(VARS_BATTLE_STATE, None)


def get_battle_state(ctx) -> BattleState:
    from vision_bot.runtime.context import RunContext

    assert isinstance(ctx, RunContext)
    state = ctx.vars.get(VARS_BATTLE_STATE)
    if isinstance(state, BattleState):
        return state
    state = BattleState()
    ctx.vars[VARS_BATTLE_STATE] = state
    return state
