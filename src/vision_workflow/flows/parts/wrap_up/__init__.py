"""子流程：收尾。"""

from vision_workflow.flows.parts.wrap_up.actions import action_log_done
from vision_workflow.module import END, OK, Flow, Module, onward

FLOW = Flow(
    id="wrap_up",
    name="收尾",
    entry="done",
    modules=[
        Module(id="done", event=action_log_done, on={OK: onward}),
    ],
    success=END,
)
