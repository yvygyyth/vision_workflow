"""键盘事件（独立于运行时上下文）。"""

from __future__ import annotations

from collections.abc import Callable

from vision_bot.core.input import press_key as _press_key
from vision_bot.runtime.cancel import raise_if_cancelled, sleep_interruptible
from vision_bot.runtime.result import Result


def press_key(key: str) -> Result:
    _press_key(key)
    return Result.success()


def press_esc(
    *,
    times: int = 1,
    pause: float = 0.2,
    cancelled: Callable[[], bool] | None = None,
) -> Result:
    for _ in range(times):
        raise_if_cancelled(cancelled)
        _press_key("esc")
        sleep_interruptible(cancelled, pause)
    return Result.success()
