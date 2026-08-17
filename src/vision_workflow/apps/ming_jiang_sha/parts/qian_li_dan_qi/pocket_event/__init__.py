"""子流程：千里单骑锦囊事件（袋子）。"""

from vision_workflow.apps.ming_jiang_sha.parts.qian_li_dan_qi.pocket_event.actions import (
    ENTER_BATTLE,
    check_after_pattern,
    click_ok,
    pick_event_pattern,
)
from vision_workflow.module import Flow, Module, ModuleConfig, abort, to
from vision_workflow.status import FULFILLED, REJECTED

FLOW = Flow(
    id="pocket_event",
    name="锦囊事件",
    description="点花纹 → 取消进战斗 / 确认回三选一（见二者后不再有花纹）",
    entry="pick_event_pattern",
    modules=[
        Module(
            id="pick_event_pattern",
            name="随机点花纹",
            description="多轮识别 event_pattern，随机点一个；没有则去看取消/确认",
            event=pick_event_pattern,
            on={
                "clicked": to("check_after"),
                "check": to("check_after"),
                REJECTED: abort,
            },
        ),
        Module(
            id="check_after",
            name="看取消或确认",
            description="cancel→战斗；ok→点确认；都没有则继续点花纹或结束",
            event=check_after_pattern,
            on={
                ENTER_BATTLE: lambda m: m.end(),
                "need_ok": to("click_ok"),
                "continue": to("pick_event_pattern"),
                FULFILLED: lambda m: m.end(),
                REJECTED: abort,
            },
        ),
        Module(
            id="click_ok",
            name="点确认",
            description="点击 ok.png，结束后回三选一（不会再点花纹）",
            event=click_ok,
            on={
                FULFILLED: lambda m: m.end(),
                REJECTED: abort,
            },
            config=ModuleConfig(
                retry=3,
                retry_delay_ms=300,
                retry_on=[REJECTED],
            ),
        ),
    ],
)
