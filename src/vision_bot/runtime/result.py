"""统一执行结果（actions / runtime 共用）。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class Result:
    ok: bool
    message: str = ""
    value: Any = None

    @classmethod
    def success(cls, message: str = "", *, value: Any = None) -> Result:
        return cls(ok=True, message=message, value=value)

    @classmethod
    def fail(cls, message: str = "", *, value: Any = None) -> Result:
        return cls(ok=False, message=message, value=value)

    @property
    def failed(self) -> bool:
        return not self.ok
