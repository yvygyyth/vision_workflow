"""识图等待（供 move 动作链使用）。"""

from __future__ import annotations

import logging
from pathlib import Path

from vision_bot.actions.context import ActionContext
from vision_bot.core.models import MatchResult
from vision_bot.vision.find import search

logger = logging.getLogger(__name__)


def wait_image(
    ctx: ActionContext,
    images: tuple[str, ...],
    *,
    threshold: float,
    timeout: float,
    interval: float,
    region: tuple[int, int, int, int] | None,
    grayscale: bool | None,
) -> MatchResult | None:
    """超时内按优先级轮询模板；命中返回结果，否则 None。"""
    if not images:
        raise ValueError("至少需要一张模板图")
    labels = "/".join(Path(p).name for p in images)
    result = search(
        *images,
        base_dir=ctx.base_dir,
        defaults=ctx.defaults,
        cancelled=ctx.cancelled,
        threshold=threshold,
        timeout=timeout,
        interval=interval,
        region=region,
        grayscale=grayscale,
    )
    ctx.value = result.value
    if result.ok:
        return result.value
    ctx.reason = result.message or f"识图未找到 [{labels}]"
    logger.info("未找到 [%s]", labels)
    return None
