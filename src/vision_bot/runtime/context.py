"""运行时上下文。"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

from vision_bot.actions.context import ActionContext
from vision_bot.core.models import MatchOptions
from vision_bot.perception.signal import SignalRegistry

if TYPE_CHECKING:
    from vision_bot.runtime.registry import FlowRegistry


@dataclass
class RunContext:
    base_dir: Path
    registry: SignalRegistry
    defaults: MatchOptions = field(default_factory=MatchOptions)
    vars: dict[str, Any] = field(default_factory=dict)
    cancel_event: threading.Event | None = None
    params: dict[str, Any] = field(default_factory=dict)
    _flow_registry: FlowRegistry | None = field(default=None, repr=False)
    _runner: Any = field(default=None, repr=False)

    def cancelled(self) -> bool:
        return self.cancel_event is not None and self.cancel_event.is_set()

    def check_cancelled(self) -> None:
        from vision_bot.runtime.cancel import raise_if_cancelled

        raise_if_cancelled(self.cancelled)

    def sleep(self, seconds: float, *, interval: float = 0.1) -> None:
        from vision_bot.runtime.cancel import sleep_interruptible

        sleep_interruptible(self.cancelled, seconds, interval=interval)

    def action_ctx(self) -> ActionContext:
        return ActionContext(
            base_dir=self.base_dir,
            defaults=self.defaults,
            vars=self.vars,
            cancelled=self.cancelled,
        )

    def snap(self, signal_ids: set[str] | None = None):
        """按需截屏识图；signal_ids 为 None 时匹配 registry 全部 signal。"""
        from vision_bot.perception.snapshot import capture

        return capture(self.registry, self.base_dir, signal_ids)

    def goto(self, target_id: str) -> None:
        if self._runner is None:
            raise RuntimeError("goto 需要在 run_root 内调用")
        self._runner.goto(target_id)

    def call(self, target_id: str) -> None:
        if self._runner is None:
            raise RuntimeError("call 需要在 run_root 内调用")
        self._runner.call(target_id)
