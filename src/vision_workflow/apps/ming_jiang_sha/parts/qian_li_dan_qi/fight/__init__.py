"""子流程：千里单骑战斗（选关后的开打 / 结算）。

- FLOW：完整开打（含赠礼）
- FLOW_IN_BATTLE：正在战斗（取消→结算，无赠礼），供事件等复用
"""

from vision_workflow.apps.ming_jiang_sha.common.actions import confirm
from vision_workflow.apps.ming_jiang_sha.parts.qian_li_dan_qi.fight.actions import (
    choose_reward_kind,
    choose_reward_title,
    click_auto,
    click_cancel,
    click_challenge_end,
    click_next_step,
    click_setting,
    move_aside,
)
from vision_workflow.module import Flow, Module, ModuleConfig, OutcomeFn, abort, onward, to
from vision_workflow.status import FULFILLED, REJECTED

_CLICK = {FULFILLED: onward, REJECTED: abort}
_END = {FULFILLED: lambda m: m.end(), REJECTED: abort}


def _in_battle_modules(
    *,
    after_settle: dict[object, OutcomeFn],
) -> list[Module]:
    """取消 → 设置/托管 → 挑战结束 → 下一步 → 结算确认。"""
    return [
        Module(
            id="click_cancel",
            name="取消",
            description="点取消",
            event=click_cancel,
            on=_CLICK,
            config=ModuleConfig(delay_ms=500),
        ),
        Module(
            id="click_setting",
            name="点设置",
            description="识别并点击 setting；成功后等 500ms",
            event=click_setting,
            on=_CLICK,
            config=ModuleConfig(delay_ms=500),
        ),
        Module(
            id="click_auto",
            name="托管",
            description="点击自动战斗；找不到则回到点设置",
            event=click_auto,
            on={FULFILLED: onward, REJECTED: to("click_setting")},
        ),
        Module(
            id="click_challenge_end",
            name="挑战结束",
            description="最长约 10 分钟、每 5 秒轮询 challenge_end 并点击",
            event=click_challenge_end,
            on=_CLICK,
            config=ModuleConfig(delay_ms=500),
        ),
        Module(
            id="next_step",
            name="下一步",
            description="点击「点击空白区域到下一步」",
            event=click_next_step,
            on=_CLICK,
        ),
        Module(
            id="settle_confirm",
            name="确认",
            description="结算确认",
            event=click_next_step,
            on=after_settle,
            config=ModuleConfig(delay_ms=1500),
        ),
    ]


FLOW = Flow(
    id="fight",
    name="开打",
    description="确认进战 → 托管 → 等结束 → 下一步 / 确认 / 选赠礼",
    entry="confirm",
    modules=[
        Module(
            id="confirm",
            name="确认",
            description="公共确认框",
            event=confirm,
            on=_CLICK,
        ),
        Module(
            id="move_aside",
            name="移开鼠标",
            description="移到 (80,80)，避免挡住识图（勿用 0,0，会触发 FailSafe）",
            event=move_aside,
            on=_CLICK,
            config=ModuleConfig(delay_ms=500),
        ),
        *_in_battle_modules(after_settle=_CLICK),
        Module(
            id="choose_reward_title",
            name="选择赠礼武将",
            description="OCR 三槽标题，按优先表与背包点击武将，并写入 ctx.vars",
            event=choose_reward_title,
            on=_CLICK,
            config=ModuleConfig(delay_ms=200),
        ),
        Module(
            id="choose_reward_kind",
            name="选择赠礼类别",
            description="识图信物/并肩作战/武将牌/资助/驰援，按武将关键奖励与背包点击",
            event=choose_reward_kind,
            on=_CLICK,
        ),
    ],
)

FLOW_IN_BATTLE = Flow(
    id="in_battle",
    name="正在战斗",
    description="取消 → 托管 → 结算确认（不含赠礼）",
    entry="click_cancel",
    modules=_in_battle_modules(after_settle=_END),
)
