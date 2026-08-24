"""输入事件（独立于运行时上下文）。"""

from vision_bot.events.keyboard import press_esc, press_key
from vision_bot.events.mouse import click_at, click_below_box, click_match

__all__ = [
    "click_at",
    "click_below_box",
    "click_match",
    "press_esc",
    "press_key",
]
