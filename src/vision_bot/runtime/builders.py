"""构建 Flow / Module 的便捷工厂。"""

from __future__ import annotations

from collections.abc import Callable

from vision_bot.runtime.context import RunContext
from vision_bot.runtime.flow import Flow, Node, RelocateFn
from vision_bot.runtime.module import Module
from vision_bot.runtime.result import Result

ActiveFn = Callable[[RunContext], Result]


def mod(id: str, name: str, active: ActiveFn) -> Module:
    return Module(id=id, name=name, active=active)


def flow(
    id: str,
    name: str,
    children: list[Node],
    *,
    relocate: list[RelocateFn] | None = None,
) -> Flow:
    return Flow(id=id, name=name, children=children, relocate=relocate or [])
