"""子流程：千里单骑战斗（选关后的开打 / 结算）。

一份模块链；用入参 ``FightGift`` 区分有无赠礼。
编排侧可用工厂生成 ``fight`` / ``in_battle`` 两个 Flow 实例（入口与入参不同）。

下一步后仍有确认框 → ``run_ended``；否则按赠礼分支，回三选一。
"""

from __future__ import annotations

from vision_workflow.apps.ming_jiang_sha.common.actions import confirm
from vision_workflow.apps.ming_jiang_sha.parts.qian_li_dan_qi.fight.actions import (
    after_settle_branch,
    check_run_end,
    choose_reward_kind,
    choose_reward_title,
    click_auto,
    click_cancel,
    click_challenge_end,
    click_next_step,
    click_setting,
    move_aside,
)
from vision_workflow.apps.ming_jiang_sha.parts.qian_li_dan_qi.fight.params import (
    PARAM_GIFT,
    FightGift,
)
from vision_workflow.apps.ming_jiang_sha.parts.qian_li_dan_qi.run_ended import RUN_ENDED
from vision_workflow.module import Flow, Module, abort, onward, to
from vision_workflow.status import FULFILLED, REJECTED

_CLICK = {FULFILLED: onward, REJECTED: abort}
_END = {FULFILLED: lambda m: m.end(), REJECTED: abort}


def _fight_modules() -> list[Module]:
    """完整模块链：确认进战 → 托管结算 → 本轮结束判定 / 赠礼分支。"""
    return [
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
        ),
        Module(
            id="click_cancel",
            name="取消",
            description="点取消",
            event=click_cancel,
            on=_CLICK,
        ),
        Module(
            id="click_setting",
            name="点设置",
            description="识别并点击 setting；成功后等 500ms",
            event=click_setting,
            on=_CLICK,
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
            name="结算确认",
            description="再点一次空白/下一步，随后判定是否本轮结束",
            event=click_next_step,
            on={FULFILLED: to("check_run_end"), REJECTED: to("check_run_end")},
        ),
        Module(
            id="check_run_end",
            name="本轮结束判定",
            description="仍有公共确认框 → run_ended；否则走赠礼/回三选一",
            event=check_run_end,
            on={
                RUN_ENDED: lambda m: m.end(),
                FULFILLED: to("after_settle"),
                REJECTED: abort,
            },
        ),
        Module(
            id="after_settle",
            name="结算分支",
            description="无赠礼/识不到→结束回三选一；有赠礼→选赠礼",
            event=after_settle_branch,
            on={
                FULFILLED: lambda m: m.end(),
                "has_gift": to("choose_reward_title"),
                REJECTED: abort,
            },
        ),
        Module(
            id="choose_reward_title",
            name="选择赠礼武将",
            description="OCR 三槽标题选武将；识不到则结束回三选一",
            event=choose_reward_title,
            on={
                FULFILLED: to("choose_reward_kind"),
                "no_gift": to("settle_done"),
                REJECTED: abort,
            },
        ),
        Module(
            id="choose_reward_kind",
            name="选择赠礼类别",
            description="识图信物/并肩作战/武将牌/资助/驰援，按武将关键奖励与背包点击",
            event=choose_reward_kind,
            on=_END,
        ),
        Module(
            id="settle_done",
            name="结算结束",
            description="对外 fulfilled，回三选一继续判断",
            event=lambda m: FULFILLED,
            on=_END,
        ),
    ]


def build_fight_flow(
    *,
    id: str,
    gift: FightGift,
    entry: str,
    name: str,
    description: str,
) -> Flow:
    """同一套模块，按入口与赠礼入参生成 Flow 实例。"""
    return Flow(
        id=id,
        name=name,
        description=description,
        entry=entry,
        params={PARAM_GIFT: gift},
        modules=_fight_modules(),
    )


FLOW = build_fight_flow(
    id="fight",
    gift=FightGift.WITH,
    entry="confirm",
    name="开打",
    description="确认进战 → 托管 → 结算 → 本轮结束判定 / 选赠礼",
)

FLOW_IN_BATTLE = build_fight_flow(
    id="in_battle",
    gift=FightGift.WITHOUT,
    entry="click_cancel",
    name="正在战斗",
    description="取消 → 托管 → 结算 → 本轮结束判定（无赠礼）",
)

__all__ = [
    "PARAM_GIFT",
    "FightGift",
    "FLOW",
    "FLOW_IN_BATTLE",
    "build_fight_flow",
]
