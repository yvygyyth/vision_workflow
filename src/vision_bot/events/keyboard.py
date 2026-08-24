"""键盘事件（独立于运行时上下文）。"""

from __future__ import annotations

from vision_bot.core.input import press_key as _press_key
from vision_bot.events.session import cancelled as default_cancelled
from vision_bot.runtime.cancel import raise_if_cancelled, sleep_interruptible
from vision_bot.runtime.result import Result


def press_key(key: str) -> Result:
    """按下并松开一个键。

    Parameters
    ----------
    key:
        键名，如 ``"esc"``、``"enter"``、``"space"``（与 pyautogui 一致）。

    Returns
    -------
    Result
        始终 ``ok=True``（按键本身无识图判定）。
    """
    _press_key(key)
    return Result.success()


def press_esc(*, times: int = 1, pause: float = 0.2) -> Result:
    """连按 Esc（关闭弹窗 / 返回）。

    Parameters
    ----------
    times:
        按键次数，默认 ``1``。
    pause:
        每次按键后的间隔秒数，默认 ``0.2``。等待期间会检查已 bind 的
        取消回调。

    Returns
    -------
    Result
        正常完成时 ``ok=True``；用户取消时抛出
        :class:`~vision_bot.runtime.cancel.CancelledError`。
    """
    cancelled = default_cancelled()
    for _ in range(times):
        raise_if_cancelled(cancelled)
        _press_key("esc")
        sleep_interruptible(cancelled, pause)
    return Result.success()
