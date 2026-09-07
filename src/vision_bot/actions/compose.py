"""顺序组合动作。"""

from __future__ import annotations

from typing import Protocol

from vision_bot.actions.context import ActionContext, resolve_action_context
from vision_bot.actions.fn import ActionFn
from vision_bot.runtime.result import Result


class Executable(Protocol):
    def execute(self) -> ActionFn: ...


class DoRunner(Protocol):
    """``do(...)()`` 可无参调用；类型上保留可选 ``ctx``。"""

    def __call__(self, ctx: ActionContext | None = None) -> Result: ...


def do(*steps: ActionFn | Executable) -> DoRunner:
    fns: list[ActionFn] = [
        s.execute() if hasattr(s, "execute") else s  # type: ignore[arg-type]
        for s in steps
    ]

    def _run(ctx: ActionContext | None = None) -> Result:
        act = resolve_action_context(ctx)
        for fn in fns:
            result = fn(act)
            if not result.ok:
                return result
        return Result.success()

    return _run
