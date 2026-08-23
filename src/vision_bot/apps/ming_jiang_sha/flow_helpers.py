"""Flow 步骤常用辅助。"""

from __future__ import annotations

from vision_bot.actions import click, do, move
from vision_bot.actions.anchor import resolve_anchor
from vision_bot.core.input import Mouse
from vision_bot.runtime.flow import StepResult


def do_click(
    ctx,
    *images: str,
    timeout: float = 3.0,
    interval: float = 0.5,
    threshold: float = 0.8,
) -> StepResult:
    act = ctx.action_ctx()
    if not images:
        return StepResult.fail("未指定模板图")
    builder = move()
    for image in images:
        builder = builder.image(image)
    outcome = do(
        builder.match(timeout=timeout, interval=interval, threshold=threshold),
        click(),
    )(act)
    if not outcome.ok:
        return StepResult.fail(act.reason or "识图点击失败")
    return StepResult.ok()


def scroll_center(ctx, amount: int, *, times: int = 1) -> StepResult:
    cx, cy = resolve_anchor("center")
    chain = Mouse().move(cx, cy)
    for _ in range(times):
        chain = chain.scroll(amount).sleep(0.05)
    chain.perform()
    return StepResult.ok()
