"""千里单骑 · 妃妃事件动作（逻辑待补）。"""

from __future__ import annotations

from vision_workflow.module import ModuleContext
from vision_workflow.status import FULFILLED, OutcomeKey


def finish_placeholder(m: ModuleContext) -> OutcomeKey:
    m.reason = "妃妃事件逻辑待补"
    return FULFILLED
