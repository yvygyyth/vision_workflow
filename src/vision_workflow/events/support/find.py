"""事件共享：识图等待等。"""

from __future__ import annotations

import time
from pathlib import Path

from vision_workflow.models.flow import MatchResult
from vision_workflow.module import ModuleContext


def find_kw(
    *,
    threshold: float,
    region: tuple[int, int, int, int] | None,
    grayscale: bool | None,
) -> dict:
    kw: dict = {"threshold": threshold}
    if region is not None:
        kw["region"] = region
    if grayscale is not None:
        kw["grayscale"] = grayscale
    return kw


def wait_image(
    m: ModuleContext,
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
    kw = find_kw(threshold=threshold, region=region, grayscale=grayscale)
    labels = "/".join(Path(p).name for p in images)
    deadline = time.monotonic() + max(timeout, 0.0)
    last: MatchResult | None = None

    while True:
        for path in images:
            hit = m.find(path, timeout=0.0, **kw)
            last = hit
            if hit.found:
                if len(images) > 1:
                    m.log("命中 [%s]", Path(path).name)
                m.value = hit
                return hit
        if timeout <= 0 or time.monotonic() >= deadline:
            m.value = last
            m.log("未找到 [%s]", labels)
            return None
        m.sleep(interval)
