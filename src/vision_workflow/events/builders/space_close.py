"""按 Esc 关闭弹窗（语义名 space_close，不识图）。"""

from __future__ import annotations

from vision_workflow.events.support.keys import press_esc_event
from vision_workflow.module import EventFn


def space_close(*, pause: float = 0.2) -> EventFn:
    """关闭弹窗：发送 Esc，再可选等待。"""
    return press_esc_event("space_close", pause=pause)
