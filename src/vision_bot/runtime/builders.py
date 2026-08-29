"""构建 Flow / Module 的便捷工厂。"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from vision_bot.runtime.context import RunContext
from vision_bot.runtime.flow import Flow, Node
from vision_bot.runtime.module import Module
from vision_bot.runtime.relocate import RelocateRule
from vision_bot.runtime.result import Result

ActiveFn = Callable[[RunContext], Result]


def mod(id: str, name: str, active: ActiveFn) -> Module:
    return Module(id=id, name=name, active=active)


def flow(
    id: str,
    name: str,
    params: dict[str, Any] | None = None,
    relocate: list[RelocateRule] | None = None,
    *,
    children: list[Node],
) -> Flow:
    return Flow(
        id=id,
        name=name,
        params=params or {},
        relocate=relocate,
        children=children,
    )
