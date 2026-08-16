"""顺序组合多个事件：任一步非 fulfilled 则短路返回。"""

from __future__ import annotations

from typing import Protocol

from vision_workflow.module import EventFn, ModuleContext
from vision_workflow.status import FULFILLED, OutcomeKey


class _Executable(Protocol):
    def execute(self) -> EventFn: ...


def do(*steps: EventFn | _Executable) -> EventFn:
    """``do(move().image(...), click())`` → 单条 Module.event。"""
    fns: list[EventFn] = [
        s.execute() if hasattr(s, "execute") else s  # type: ignore[arg-type]
        for s in steps
    ]

    def _event(m: ModuleContext) -> OutcomeKey:
        for fn in fns:
            key = fn(m)
            if key != FULFILLED:
                return key
        return FULFILLED

    return _event
