"""鼠标事件（独立于运行时上下文）。"""

from __future__ import annotations

from vision_bot.core.input import Mouse
from vision_bot.core.models import MatchResult
from vision_bot.runtime.result import Result


def click_at(x: int, y: int, *, pause: float = 0.2) -> Result:
    Mouse().move(x, y).click().sleep(pause).perform()
    return Result.success()


def click_match(hit: MatchResult, *, pause: float = 0.2) -> Result:
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
    if not hit.found or not hit.box:
        return Result.fail("无有效匹配区域")
    x, y, w, h = hit.box
    return click_at(x + w // 2, y + h + offset_y, pause=pause)
