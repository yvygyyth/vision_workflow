"""Flow 步骤常用辅助。"""

from __future__ import annotations

from vision_bot.actions.anchor import resolve_anchor
from vision_bot.core.input import Mouse
from vision_bot.runtime.result import Result


def scroll_center(amount: int, *, times: int = 1) -> Result:
    """在屏幕中心滚动鼠标滚轮。"""
    cx, cy = resolve_anchor("center")
    chain = Mouse().move(cx, cy)
    for _ in range(times):
        chain = chain.scroll(amount).sleep(0.05)
    chain.perform()
    return Result.success()
