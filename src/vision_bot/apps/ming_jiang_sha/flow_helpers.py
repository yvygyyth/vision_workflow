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
    """等待模板出现后点击其中心点。

    Parameters
    ----------
    ctx:
        运行上下文（保留参数以兼容现有 flow 步骤签名；识图默认值已由
        ``run_root`` bind，此处不再读取 ctx 字段）。
    *images:
        一个或多个模板图路径，传给 :func:`vision.wait_any`。
    timeout:
        最长等待秒数，默认 ``3.0``。
    interval:
        轮询间隔秒数，默认 ``0.5``。
    threshold:
        匹配分数下限，默认 ``0.8``。

    Returns
    -------
    Result
        识图并点击成功时 ``ok=True``；未找到模板时 ``ok=False``。
    """
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
    """在屏幕中心滚动鼠标滚轮。

    Parameters
    ----------
    ctx:
        运行上下文（保留以兼容步骤签名，未使用）。
    amount:
        滚动量；正数向上，负数向下。
    times:
        重复滚动次数，默认 ``1``。

    Returns
    -------
    Result
        始终 ``ok=True``。
    """
    cx, cy = resolve_anchor("center")
    chain = Mouse().move(cx, cy)
    for _ in range(times):
        chain = chain.scroll(amount).sleep(0.05)
    chain.perform()
    return Result.success()
