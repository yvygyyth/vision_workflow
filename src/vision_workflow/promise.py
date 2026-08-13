"""中间件 / Runner 内部的结算结果。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from vision_workflow.status import EventStatus


@dataclass
class Settled:
    """一轮模块/流程执行的成功或失败结果。"""

    ok: bool
    value: Any = None
    error: str = ""
    feedback: str = ""

    @property
    def status(self) -> EventStatus:
        """对应事件层结算状态（由 ok 映射，不与 FlowStatus 混用）。"""
        return EventStatus.from_ok(self.ok)

    @classmethod
    def resolve(cls, value: Any = None, feedback: str = "") -> Settled:
        return cls(
            ok=True,
            value=value,
            feedback=feedback or EventStatus.FULFILLED.value,
        )

    @classmethod
    def reject(cls, error: str = "", value: Any = None, feedback: str = "") -> Settled:
        return cls(
            ok=False,
            value=value,
            error=error or EventStatus.REJECTED.value,
            feedback=feedback or error or EventStatus.REJECTED.value,
        )
