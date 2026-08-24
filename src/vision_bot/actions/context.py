"""动作执行上下文（供动作链组合使用）。"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from vision_bot.core.models import MatchOptions


@dataclass
class ActionContext:
    """动作链运行时状态（路径默认值、取消信号、临时变量）。"""

    base_dir: Path
    defaults: MatchOptions = field(default_factory=MatchOptions)
    vars: dict[str, Any] = field(default_factory=dict)
    cancelled: Callable[[], bool] = field(default_factory=lambda: (lambda: False))
    reason: str = ""
    value: Any = None
