"""跳转控制。"""

from __future__ import annotations

import builtins
from dataclasses import dataclass
from enum import Enum, auto
from typing import Literal


@dataclass
class Jump(Exception):
    kind: Literal["goto", "call"]
    target_id: str


class JumpTargetError(RuntimeError):
    """goto/call 目标不存在，终止本次运行。"""


class Relocate(Enum):
    """relocate 规则的特殊返回值。"""

    PARENT = auto()
    """交给父 Flow 的 relocate；根节点无父时停止本次运行。"""


class RelocateStop(Exception):
    """根节点 relocate 返回 PARENT，停止本次运行。"""

    def __init__(self, message: str = "根节点 relocate 返回 PARENT，已停止") -> None:
        super().__init__(message)


def _install_parent_builtin() -> None:
    """挂到 builtins，业务可直接 ``return PARENT``，无需 import。"""
    builtins.PARENT = Relocate.PARENT  # type: ignore[attr-defined]


_install_parent_builtin()
