"""跳转控制。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass
class Jump(Exception):
    kind: Literal["goto", "call"]
    target_id: str


class JumpTargetError(RuntimeError):
    """goto/call 目标不存在，终止本次运行。"""
