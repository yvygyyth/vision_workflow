"""按 Esc 返回上一步（语义名 go_back，不识图）。"""

from __future__ import annotations

from vision_workflow.events.support.keys import press_esc_event
from vision_workflow.module import EventFn


def go_back(*, pause: float = 0.2) -> EventFn:
    """返回上一步：发送 Esc，再可选等待。"""
    return press_esc_event("go_back", pause=pause)
