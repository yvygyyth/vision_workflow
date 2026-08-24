"""输入事件模块默认配置。

任务启动时通过 :func:`events.bind` 注入取消回调；``press_esc`` 等会据此
响应用户停止。
"""

from __future__ import annotations

from collections.abc import Callable

_cancelled: Callable[[], bool] | None = None


def bind(*, cancelled: Callable[[], bool] | None = None) -> None:
    """绑定输入事件的取消回调（任务启动时调用一次即可）。

    Parameters
    ----------
    cancelled:
        取消检查函数，签名 ``() -> bool``。返回 ``True`` 时，
        ``press_esc`` 等带等待的按键操作会立即中断。
    """
    global _cancelled
    if cancelled is not None:
        _cancelled = cancelled


def cancelled() -> Callable[[], bool] | None:
    """返回当前绑定的取消回调（一般无需直接访问）。"""
    return _cancelled
