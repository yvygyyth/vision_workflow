"""识图等待（供 move 等动作使用）。"""

from __future__ import annotations

import logging
import time
from pathlib import Path

from vision_bot.actions.context import ActionContext
from vision_bot.core.models import MatchResult

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
    kw: dict = {"threshold": threshold}
    if region is not None:
        kw["region"] = region
    if grayscale is not None:
        kw["grayscale"] = grayscale
    labels = "/".join(Path(p).name for p in images)
    deadline = time.monotonic() + max(timeout, 0.0)
    last: MatchResult | None = None

    while True:
        for path in images:
            hit = ctx.find(path, timeout=0.0, **kw)
            last = hit
            if hit.found:
                if len(images) > 1:
                    logger.info("命中 [%s]", Path(path).name)
                ctx.value = hit
                return hit
        if timeout <= 0 or time.monotonic() >= deadline:
            ctx.value = last
            ctx.reason = f"识图未找到 [{labels}]"
            logger.info("未找到 [%s]", labels)
            return None
        time.sleep(interval)
