"""子流程：千里单骑本轮结束。"""

from vision_workflow.apps.ming_jiang_sha.common.actions import confirm, space_close
from vision_workflow.module import Flow, Module, to
from vision_workflow.status import FULFILLED, REJECTED

# 兼作 Module / Flow 路由 key
RUN_ENDED = "run_ended"

FLOW = Flow(
    id="run_ended",
    name="本轮结束",
    description="点结算确认 → 关弹窗 → 交给进战开下一局",
    entry="confirm",
    modules=[
        Module(
            id="confirm",
            name="本轮结束确认",
            description="公共确认框；没有也继续关弹窗",
            event=confirm,
            on={
                FULFILLED: to("close"),
                REJECTED: to("close"),
            },
        ),
        Module(
            id="close",
            name="关闭空白弹窗",
            description="Esc 关弹窗后结束本 Flow",
            event=space_close(),
            on={
                FULFILLED: lambda m: m.end(),
                REJECTED: lambda m: m.end(),
            },
        ),
    ],
)
