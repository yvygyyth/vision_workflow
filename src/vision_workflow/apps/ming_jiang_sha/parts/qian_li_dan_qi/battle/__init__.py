"""子流程：千里单骑战斗界面。"""

from vision_workflow.apps.ming_jiang_sha.parts.qian_li_dan_qi.battle.state import (
    bind_battle_state,
    clear_battle_state,
    get_battle_state,
)
from vision_workflow.module import Flow, FlowLifecycle, Module, onward
from vision_workflow.status import FULFILLED


def _placeholder(m):
    """战斗逻辑待补充；先占位成功结束。"""
    state = get_battle_state(m.ctx)
    m.log(
        "battle flow placeholder tokens=%s buffs=%s copper=%s",
        state.critical_tokens,
        state.buffs,
        state.copper_coins,
    )
    return FULFILLED


FLOW = Flow(
    id="battle",
    name="战斗",
    description="千里单骑战斗界面",
    entry="ready",
    lifecycle=FlowLifecycle(
        on_enter=bind_battle_state,
        on_exit=clear_battle_state,
    ),
    modules=[
        Module(
            id="ready",
            name="进入战斗",
            description="已进入战斗界面（逻辑待补充）",
            event=_placeholder,
            on={FULFILLED: onward},
        ),
    ],
)
