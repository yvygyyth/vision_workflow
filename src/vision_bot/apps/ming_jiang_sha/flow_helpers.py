"""Flow 步骤常用辅助。"""

from __future__ import annotations

from vision_bot.actions.anchor import resolve_anchor
from vision_bot.core.input import Mouse
from vision_bot.events import click_match
from vision_bot.runtime.result import Result
from vision_bot.vision import wait_any


def do_click(
    ctx,
    *images: str,
    timeout: float = 3.0,
    interval: float = 0.5,
    threshold: float = 0.8,
) -> Result:
    if not images:
        return Result.fail("未指定模板图")
    result = wait_any(
        *images,
        timeout=timeout,
        interval=interval,
        threshold=threshold,
    )
    if not result.ok:
        return result
    return click_match(result.value)


def scroll_center(ctx, amount: int, *, times: int = 1) -> Result:
    cx, cy = resolve_anchor("center")
    chain = Mouse().move(cx, cy)
    for _ in range(times):
        chain = chain.scroll(amount).sleep(0.05)
    chain.perform()
    return Result.success()
