"""子流程：失败处理。"""

from config.flow.handle_fail.actions import action_handle_fail
from vision_workflow.module import END, Flow, Module

FLOW = Flow(
    id="handle_fail",
    name="失败处理",
    entry="report",
    modules=[
        Module(id="report", event=action_handle_fail, success=END),
    ],
    success=END,
)
