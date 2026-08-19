"""子流程：千里单骑 · 墨子事件。"""

from vision_workflow.apps.ming_jiang_sha.common.actions import confirm
from vision_workflow.apps.ming_jiang_sha.parts.qian_li_dan_qi.mo_zi.actions import (
    click_option,
)
from vision_workflow.module import Flow, Module, ModuleConfig, abort, onward
from vision_workflow.status import FULFILLED, REJECTED

FLOW = Flow(
    id="mo_zi",
    name="墨子事件",
    description="确认 → 等 500ms → 随机点选项 → 回三选一",
    entry="confirm",
    modules=[
        Module(
            id="confirm",
            name="确认",
            description="公共确认框；点完等 500ms",
            event=confirm,
            on={FULFILLED: onward, REJECTED: abort},
            config=ModuleConfig(delay_ms=500),
        ),
        Module(
            id="click_option",
            name="点选项",
            description="在 (1130,360)/(1130,630)/(1130,900) 中随机点一次",
            event=click_option,
            on={
                FULFILLED: lambda m: m.end(),
                REJECTED: abort,
            },
        ),
    ],
)
