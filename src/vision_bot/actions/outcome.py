"""动作结果。"""

from __future__ import annotations

from enum import Enum
from typing import Any

from dataclasses import dataclass


class ActionStatus(str, Enum):
    OK = "ok"
    FAIL = "fail"


@dataclass
class ActionOutcome:
    status: ActionStatus
    reason: str = ""
    value: Any = None

    @property
    def ok(self) -> bool:
        return self.status is ActionStatus.OK

    @classmethod
    def success(cls, *, reason: str = "", value: Any = None) -> ActionOutcome:
        return cls(ActionStatus.OK, reason=reason, value=value)

    @classmethod
    def failed(cls, *, reason: str = "", value: Any = None) -> ActionOutcome:
        return cls(ActionStatus.FAIL, reason=reason, value=value)


ActionFn = "Callable[[ActionContext], ActionOutcome]"
