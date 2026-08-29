"""输入事件公共 API。

使用前需先 :func:`bind` 绑定取消回调（:func:`~vision_bot.runtime.runner.run` 会自动完成）。
返回值统一为 :class:`~vision_bot.runtime.result.Result`。
"""

from vision_bot.events.keyboard import press_esc, press_key
from vision_bot.events.mouse import (
    CursorKind,
    CursorState,
    click_at,
    click_below_box,
    click_match,
    cursor_is_hidden,
    cursor_is_pointer,
    get_cursor_state,
)
from vision_bot.events.session import bind

__all__ = [
    "CursorKind",
    "CursorState",
    "bind",
    "click_at",
    "click_below_box",
    "click_match",
    "cursor_is_hidden",
    "cursor_is_pointer",
    "get_cursor_state",
    "press_esc",
    "press_key",
]
