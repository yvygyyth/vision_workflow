"""任务取消。"""

from __future__ import annotations

import time
from collections.abc import Callable


class CancelledError(Exception):
    """用户请求停止。"""


def raise_if_cancelled(cancelled: Callable[[], bool] | None) -> None:
    if cancelled and cancelled():
        raise CancelledError()


def sleep_interruptible(
    cancelled: Callable[[], bool] | None,
    seconds: float,
    *,
    interval: float = 0.1,
) -> None:
    """可中断 sleep；取消时抛 CancelledError。"""
    if seconds <= 0:
        raise_if_cancelled(cancelled)
        return
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        raise_if_cancelled(cancelled)
        time.sleep(min(interval, max(0.0, deadline - time.monotonic())))
