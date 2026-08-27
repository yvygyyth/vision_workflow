"""千里单骑 · 局内状态。"""

from __future__ import annotations

from dataclasses import dataclass, field

from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.utils.rewards import RewardKind

VARS_BATTLE_STATE = "battle_state"


@dataclass
class BattleState:
    copper_coins: int = 0
    general_rewards: dict[str, set[RewardKind]] = field(default_factory=dict)

    def has_general_reward(self, name: str, kind: RewardKind) -> bool:
        return kind in self.general_rewards.get(name, set())

    def mark_general_reward(self, name: str, kind: RewardKind) -> None:
        self.general_rewards.setdefault(name, set()).add(kind)

    def has_reward(self, kind: RewardKind) -> bool:
        return any(kind in kinds for kinds in self.general_rewards.values())

    def mark_reward(self, kind: RewardKind) -> None:
        self.mark_general_reward("", kind)


def bind_battle_state(ctx) -> BattleState:
    state = BattleState()
    ctx.vars[VARS_BATTLE_STATE] = state
    return state


def clear_battle_state(ctx) -> None:
    ctx.vars.pop(VARS_BATTLE_STATE, None)


def get_battle_state(ctx) -> BattleState:
    state = ctx.vars.get(VARS_BATTLE_STATE)
    if isinstance(state, BattleState):
        return state
    state = BattleState()
    ctx.vars[VARS_BATTLE_STATE] = state
    return state
