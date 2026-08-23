"""流程编排。"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from vision_bot.runtime.context import RunContext
from vision_bot.runtime.module import Module

RelocateFn = Callable[[RunContext], str | None]


@dataclass
class Flow:
    id: str
    name: str
    children: list[Flow | Module]
    relocate: list[RelocateFn] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.children:
            raise ValueError(f"Flow [{self.id}] children 不可为空")


Node = Flow | Module
