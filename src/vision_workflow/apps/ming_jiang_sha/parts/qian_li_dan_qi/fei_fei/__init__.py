"""子流程：千里单骑 · 妃妃事件。"""

from vision_workflow.apps.ming_jiang_sha.common.actions import confirm
from vision_workflow.apps.ming_jiang_sha.parts.qian_li_dan_qi.fei_fei.actions import (
    choose_option,
)
from vision_workflow.module import Flow, Module, ModuleConfig, abort, onward
from vision_workflow.status import FULFILLED, REJECTED

_CLICK = {FULFILLED: onward, REJECTED: abort}

FLOW = Flow(
    id="fei_fei",
    name="妃妃事件",
    description="确认 → 按优先级点选项 → 回三选一",
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
            id="choose_option",
            name="选择选项",
            description="优先级：我来帮你 → 快睡午觉 → 讨价还价",
            event=choose_option,
            on={
                FULFILLED: lambda m: m.end(),
                REJECTED: abort,
            },
            config=ModuleConfig(
                retry=6,
                retry_delay_ms=400,
                retry_on=[REJECTED],
            ),
        ),
    ],
)
