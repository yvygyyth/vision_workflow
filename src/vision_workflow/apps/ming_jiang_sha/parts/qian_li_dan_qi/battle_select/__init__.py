"""子流程：千里单骑三选一（选完战斗后结束本 Flow，交给 fight）。"""

from vision_workflow.apps.ming_jiang_sha.parts.qian_li_dan_qi.battle_select.actions import (
    ShopChoice,
    choose_battle,
    choose_event,
    choose_shop,
    detect_choice,
)
from vision_workflow.module import Flow, Module, ModuleConfig, abort, to
from vision_workflow.status import FULFILLED, REJECTED

_BACK_TO_DETECT = {FULFILLED: to("detect_choice"), REJECTED: abort}

FLOW = Flow(
    id="battle_select",
    name="三选一",
    description="判定并点选本轮选项；战斗选完后进入 fight；袋子进入 pocket_event",
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
            on={
                FULFILLED: lambda m: m.end(),
                REJECTED: abort,
            },
        ),
        Module(
            id="choose_shop",
            name="商店选择",
            description="铜币≥30点霸青商店，否则锦囊事件，再否则休息；袋子结束本 Flow",
            event=choose_shop,
            on={
                ShopChoice.BA_QING_STORE: to("detect_choice"),
                ShopChoice.POCKET_EVENT: lambda m: m.end(),
                ShopChoice.REST: to("detect_choice"),
                REJECTED: abort,
            },
        ),
        Module(
            id="choose_event",
            name="事件选择",
            description="事件分支（逻辑待补）；完成后回到判定",
            event=choose_event,
            on=_BACK_TO_DETECT,
        ),
    ],
)
