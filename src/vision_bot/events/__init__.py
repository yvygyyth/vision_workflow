"""输入事件公共 API。

使用前需先 :func:`bind` 绑定取消回调（:func:`~vision_bot.runtime.runner.run` 会自动完成）。
返回值统一为 :class:`~vision_bot.runtime.result.Result`。
"""

from vision_bot.events.keyboard import press_esc, press_key
from vision_bot.events.mouse import click_at, click_below_box, click_match
from vision_bot.events.session import bind

__all__ = [
    "bind",
    "click_at",
    "click_below_box",
    "click_match",
    "press_esc",
    "press_key",
]
