"""中间件 / Runner 内部的结算结果。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from vision_workflow.status import EventStatus, OutcomeKey


@dataclass
class Settled:
    """一轮模块/流程执行的成功或失败结果。"""

    ok: bool
    value: Any = None
    error: str = ""
    feedback: str = ""
    key: OutcomeKey | None = None
    """模块 event 的 outcome key；流程结束时可用于 FlowRouter 自定义路由。"""

    @property
    def status(self) -> EventStatus:
        """对应事件层结算状态（由 ok 映射，不与 FlowStatus 混用）。"""
        return EventStatus.from_ok(self.ok)

    @classmethod
    def resolve(
        cls,
        value: Any = None,
        feedback: str = "",
        *,
        key: OutcomeKey | None = None,
    ) -> Settled:
        return cls(
            ok=True,
            value=value,
            feedback=feedback or EventStatus.FULFILLED.value,
            key=key,
        )

    @classmethod
    def reject(
        cls,
        error: str = "",
        value: Any = None,
        feedback: str = "",
        *,
        key: OutcomeKey | None = None,
    ) -> Settled:
        return cls(
            ok=False,
            value=value,
            error=error or EventStatus.REJECTED.value,
            feedback=feedback or error or EventStatus.REJECTED.value,
            key=key,
        )
