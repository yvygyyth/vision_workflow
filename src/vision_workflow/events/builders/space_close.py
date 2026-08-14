"""按 Esc 关闭弹窗（语义名 space_close，不识图）。"""

from __future__ import annotations

from vision_workflow.input import press_key
from vision_workflow.module import EventFn, ModuleContext
from vision_workflow.status import FULFILLED, OutcomeKey


def space_close(*, pause: float = 0.2) -> EventFn:
    """关闭弹窗：发送 Esc，再可选等待。"""

    def _event(m: ModuleContext) -> OutcomeKey:
        m.log("space_close: Esc")
        press_key("esc")
        if pause > 0:
            m.sleep(pause)
        return FULFILLED

    return _event
