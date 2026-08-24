"""输入事件模块运行时默认值。"""

from __future__ import annotations

from collections.abc import Callable

_cancelled: Callable[[], bool] | None = None


def bind(*, cancelled: Callable[[], bool] | None = None) -> None:
    global _cancelled
    if cancelled is not None:
        _cancelled = cancelled


def cancelled() -> Callable[[], bool] | None:
    return _cancelled
