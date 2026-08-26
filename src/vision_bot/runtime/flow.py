"""流程编排。"""

from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

from vision_bot.runtime.context import RunContext
from vision_bot.runtime.module import Module

if TYPE_CHECKING:
    from vision_bot.runtime.config import RunConfig
    from vision_bot.runtime.runner import RunReport

RelocateFn = Callable[[RunContext], str | None]


@dataclass(kw_only=True)
class Flow:
    id: str
    name: str
    params: dict[str, Any] = field(default_factory=dict)
    relocate: list[RelocateFn] = field(default_factory=list)
    children: list[Flow | Module]

    def __post_init__(self) -> None:
        if not self.children:
            raise ValueError(f"Flow [{self.id}] children 不可为空")

    def run(
        self,
        config: RunConfig | None = None,
        *,
        cancel_event: threading.Event | None = None,
        base_dir: Path | None = None,
    ) -> RunReport:
        from vision_bot.runtime.config import RunConfig as RC
        from vision_bot.runtime.runner import run

        return run(
            self,
            config or RC(),
            cancel_event=cancel_event,
            base_dir=base_dir,
        )


Node = Flow | Module
