"""运行时上下文。"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from vision_bot.actions.context import ActionContext
from vision_bot.core.models import MatchOptions
from vision_bot.perception.signal import SignalRegistry


@dataclass
class RunContext:
    base_dir: Path
    registry: SignalRegistry
    defaults: MatchOptions = field(default_factory=MatchOptions)
    vars: dict[str, Any] = field(default_factory=dict)
    cancel_event: threading.Event | None = None
    params: dict[str, Any] = field(default_factory=dict)

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
