"""子流程：千里单骑三选一（选完战斗后结束本 Flow，交给 fight）。"""

from vision_workflow.apps.ming_jiang_sha.parts.qian_li_dan_qi.battle_select.actions import (
    EventChoice,
    ShopChoice,
    choose_battle,
    choose_event,
    choose_shop,
    confirm_ba_qing_entered,
    confirm_event_entered,
    detect_choice,
)
from vision_workflow.module import Flow, Module, ModuleConfig, abort, to
from vision_workflow.status import FULFILLED, REJECTED

_END = {FULFILLED: lambda m: m.end(), REJECTED: abort}

FLOW = Flow(
    id="battle_select",
    name="三选一",
    description="判定并点选；战斗→fight，巴清/事件确认进入后再进对应 Flow",
    entry="detect_choice",
    modules=[
        Module(
            id="detect_choice",
            name="判定选择类型",
            description="在选择区内识别战斗/商店/事件（优先战斗）",
            event=detect_choice,
            on={
                "battle": to("choose_battle"),
                "shop": to("choose_shop"),
                "event": to("choose_event"),
                REJECTED: abort,
            },
            config=ModuleConfig(
                retry=9,
                retry_delay_ms=500,
                retry_on=[REJECTED],
            ),
        ),
        Module(
            id="choose_battle",
            name="战斗选择",
            description="有 challenge_help 点它，否则点第一个 challenge；然后结束本 Flow",
            event=choose_battle,
            on=_END,
        ),
        Module(
            id="choose_shop",
            name="商店选择",
            description="铜币≥30点巴清商店，否则锦囊事件，再否则休息；巴清去核验进店",
            event=choose_shop,
            on={
                ShopChoice.BA_QING_STORE: to("confirm_ba_qing_entered"),
                ShopChoice.POCKET_EVENT: lambda m: m.end(),
                ShopChoice.REST: to("detect_choice"),
                REJECTED: abort,
            },
        ),
        Module(
            id="confirm_ba_qing_entered",
            name="确认进入巴清",
            description="点击后看 ba_qing 图标是否消失；消失才结束本 Flow 进商店",
            event=confirm_ba_qing_entered,
            on={
                ShopChoice.BA_QING_STORE: lambda m: m.end(),
                "still_here": to("detect_choice"),
                REJECTED: abort,
            },
            config=ModuleConfig(
                retry=2,
                retry_delay_ms=400,
                retry_on=["still_here"],
            ),
        ),
        Module(
            id="choose_event",
            name="事件选择",
            description="点诸葛亮/妃妃/十常侍其一，再核验是否进入",
            event=choose_event,
            on={
                EventChoice.ZHU_GE_LIANG: to("confirm_event_entered"),
                EventChoice.FEI_FEI: to("confirm_event_entered"),
                EventChoice.SHI_CHANG_SHI: to("confirm_event_entered"),
                REJECTED: abort,
            },
        ),
        Module(
            id="confirm_event_entered",
            name="确认进入事件",
            description="点击后看对应事件图标是否消失；消失才结束本 Flow",
            event=confirm_event_entered,
            on={
                EventChoice.ZHU_GE_LIANG: lambda m: m.end(),
                EventChoice.FEI_FEI: lambda m: m.end(),
                EventChoice.SHI_CHANG_SHI: lambda m: m.end(),
                "still_here": to("detect_choice"),
                REJECTED: abort,
            },
            config=ModuleConfig(
                retry=2,
                retry_delay_ms=400,
                retry_on=["still_here"],
            ),
        ),
    ],
)
