"""鼠标事件（独立于运行时上下文）。"""

from __future__ import annotations

from vision_bot.core.input import (
    CursorKind,
    CursorState,
    Mouse,
    cursor_is_hidden,
    cursor_is_pointer,
    get_cursor_state,
)
from vision_bot.core.models import MatchResult
from vision_bot.runtime.result import Result

__all__ = [
    "CursorKind",
    "CursorState",
    "click_at",
    "click_below_box",
    "click_match",
    "cursor_is_hidden",
    "cursor_is_pointer",
    "get_cursor_state",
]

def click_at(x: int, y: int, *, pause: float = 0.2) -> Result:
    """移动鼠标到屏幕坐标并左键单击。

    Parameters
    ----------
    x:
        目标点横坐标（屏幕像素）。
    y:
        目标点纵坐标（屏幕像素）。
    pause:
        点击后等待秒数，默认 ``0.2``。

    Returns
    -------
    Result
        始终 ``ok=True``。
    """
    Mouse().move(x, y).click().sleep(pause).perform()
    return Result.success()


def click_match(hit: MatchResult, *, pause: float = 0.2) -> Result:
    """点击识图命中的中心点。

    Parameters
    ----------
    hit:
        :func:`vision.find` 返回的 ``value``。
        需 ``found=True`` 且 ``center`` 非空。
    pause:
        点击后等待秒数，默认 ``0.2``。

    Returns
    -------
    Result
        有效命中时 ``ok=True``；无中心点时 ``ok=False``，
        ``message="无有效匹配点"``。
    """
    if not hit.found or not hit.center:
        return Result.fail("无有效匹配点")
    cx, cy = hit.center
    return click_at(cx, cy, pause=pause)


def click_below_box(
    hit: MatchResult,
    *,
    offset_y: int = 0,
    pause: float = 0.2,
) -> Result:
    """点击匹配框底边中点再向下偏移（适用于 confirm 等按钮）。

    落点坐标：``(box.x + box.w // 2, box.y + box.h + offset_y)``。

    Parameters
    ----------
    hit:
        识图结果，需 ``found=True`` 且 ``box`` 非空。
    offset_y:
        相对框底边向下的额外像素偏移，默认 ``0``。
    pause:
        点击后等待秒数，默认 ``0.2``。

    Returns
    -------
    Result
        有效命中时 ``ok=True``；无匹配框时 ``ok=False``，
        ``message="无有效匹配区域"``。
    """
    if not hit.found or not hit.box:
        return Result.fail("无有效匹配区域")
    x, y, w, h = hit.box
    return click_at(x + w // 2, y + h + offset_y, pause=pause)
