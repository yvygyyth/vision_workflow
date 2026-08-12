"""子流程：收尾。"""

from config.flow.wrap_up.actions import action_log_done
from vision_workflow.module import END, Flow, Module

FLOW = Flow(
    id="wrap_up",
    name="收尾",
    entry="done",
    modules=[
        Module(id="done", event=action_log_done, success=END),
    ],
    success=END,
)
