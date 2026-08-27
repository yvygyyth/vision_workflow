"""动作执行上下文（供动作链组合使用）。"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from vision_bot.core.models import MatchOptions

_bound: ActionContext | None = None


@dataclass
class ActionContext:
    """动作链运行时状态（路径默认值、取消信号、临时变量）。"""

    base_dir: Path
    defaults: MatchOptions = field(default_factory=MatchOptions)
    vars: dict[str, Any] = field(default_factory=dict)
    cancelled: Callable[[], bool] = field(default_factory=lambda: (lambda: False))
    reason: str = ""
    value: Any = None


def bind_action_context(
    *,
    base_dir: Path,
    defaults: MatchOptions | None = None,
    vars: dict[str, Any] | None = None,
    cancelled: Callable[[], bool] | None = None,
) -> None:
    """任务启动时绑定当前动作上下文（与 :func:`vision_bot.runtime.bind.bind_runtime` 一并调用）。"""
    global _bound
    prev = _bound
    _bound = ActionContext(
        base_dir=base_dir,
        defaults=defaults if defaults is not None else (prev.defaults if prev else MatchOptions()),
        vars=vars if vars is not None else (prev.vars if prev else {}),
        cancelled=cancelled if cancelled is not None else (prev.cancelled if prev else (lambda: False)),
    )


def action_context() -> ActionContext:
    """当前任务绑定的动作上下文。"""
    if _bound is None:
        raise RuntimeError("动作上下文未绑定，请在 run() 内执行或先调用 bind_action_context")
    return _bound


def resolve_action_context(ctx: ActionContext | None = None) -> ActionContext:
    return ctx if ctx is not None else action_context()
