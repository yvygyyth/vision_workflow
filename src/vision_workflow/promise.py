"""模块生命周期结算结果。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class Settled:
    """一轮 action/judge 的成功或失败结果。"""

    ok: bool
    value: Any = None
    error: str = ""
    feedback: str = ""

    @classmethod
    def resolve(cls, value: Any = None, feedback: str = "") -> Settled:
        return cls(ok=True, value=value, feedback=feedback or "ok")

    @classmethod
    def reject(cls, error: str = "", value: Any = None, feedback: str = "") -> Settled:
        return cls(
            ok=False,
            value=value,
            error=error or "rejected",
            feedback=feedback or error or "failed",
        )
