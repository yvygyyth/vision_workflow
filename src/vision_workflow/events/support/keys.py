"""按 Esc 的共享实现。"""

from __future__ import annotations

from vision_workflow.input import press_key
from vision_workflow.module import EventFn, ModuleContext
from vision_workflow.status import FULFILLED, OutcomeKey


def press_esc_event(label: str, *, pause: float = 0.2) -> EventFn:
    """发送 Esc 并可选等待；label 仅用于日志。"""

    def _event(m: ModuleContext) -> OutcomeKey:
        m.log("%s: Esc", label)
        press_key("esc")
        if pause > 0:
            m.sleep(pause)
        return FULFILLED

    return _event
