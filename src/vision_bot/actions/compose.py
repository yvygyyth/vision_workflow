"""顺序组合动作。"""

from __future__ import annotations

from typing import Protocol

from vision_bot.actions.context import ActionContext
from vision_bot.actions.fn import ActionFn
from vision_bot.runtime.result import Result


class Executable(Protocol):
    def execute(self) -> ActionFn: ...


def do(*steps: ActionFn | Executable) -> ActionFn:
    fns: list[ActionFn] = [
        s.execute() if hasattr(s, "execute") else s  # type: ignore[arg-type]
        for s in steps
    ]

    def _run(ctx: ActionContext) -> Result:
        for fn in fns:
            result = fn(ctx)
            if not result.ok:
                return result
        return Result.success()

    return _run
