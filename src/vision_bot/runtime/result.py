"""执行结果（Module / Flow 统一）。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Result:
    ok: bool
    message: str = ""

    @classmethod
    def success(cls, message: str = "") -> Result:
        return cls(ok=True, message=message)

    @classmethod
    def fail(cls, message: str = "") -> Result:
        return cls(ok=False, message=message)

    @property
    def failed(self) -> bool:
        return not self.ok
