"""子流程：千里单骑 · 休息。"""

from vision_workflow.apps.ming_jiang_sha.parts.qian_li_dan_qi.rest.actions import (
    click_rest_slot,
)
from vision_workflow.module import Flow, Module, abort
from vision_workflow.status import FULFILLED, REJECTED

FLOW = Flow(
    id="rest",
    name="休息",
    description="随机点休息槽 → 回三选一",
    entry="click_slot",
    modules=[
        Module(
            id="click_slot",
            name="点休息槽",
            description="随机点一次",
            event=click_rest_slot,
            on={
                FULFILLED: lambda m: m.end(),
                REJECTED: abort,
            },
        ),
    ],
)
