"""顺序组合动作。"""

from __future__ import annotations

from typing import Callable, Protocol

from vision_bot.actions.context import ActionContext
from vision_bot.actions.outcome import ActionOutcome, ActionStatus

ActionFn = Callable[[ActionContext], ActionOutcome]


class Executable(Protocol):
    def execute(self) -> ActionFn: ...


def do(*steps: ActionFn | Executable) -> ActionFn:
    fns: list[ActionFn] = [
        s.execute() if hasattr(s, "execute") else s  # type: ignore[arg-type]
        for s in steps
    ]

    def _run(ctx: ActionContext) -> ActionOutcome:
        for fn in fns:
            outcome = fn(ctx)
            if not outcome.ok:
                return outcome
        return ActionOutcome(ActionStatus.OK)

    return _run
