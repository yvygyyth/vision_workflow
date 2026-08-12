"""常用事件工厂（供 Module.event 使用）。"""

from __future__ import annotations

import time
from pathlib import Path

from vision_workflow.models.flow import MatchResult
from vision_workflow.module import MISS, OK, EventFn, ModuleContext


def click_image(
    *images: str,
    threshold: float = 0.8,
    timeout: float = 3.0,
    interval: float = 0.5,
    sleep: float = 0.2,
    offset_x: int = 0,
    offset_y: int = 0,
    region: tuple[int, int, int, int] | None = None,
    grayscale: bool | None = None,
) -> EventFn:
    """识图并点击中心（可偏移），返回 OK / MISS。

    可传入多张模板，按参数顺序优先匹配；超时内命中任一即点击。

    Examples
    --------
    click_image("data/.../entry.png")
    click_image("data/.../entry.png", "data/.../entry2.png")  # 优先前者
    click_image("data/.../btn.png", offset_y=100)
    """
    if not images:
        raise ValueError("click_image() 至少需要一张模板图")

    find_kw: dict = {"threshold": threshold}
    if region is not None:
        find_kw["region"] = region
    if grayscale is not None:
        find_kw["grayscale"] = grayscale

    def _perform(m: ModuleContext, hit: MatchResult) -> str:
        m.value = hit
        if hit.center:
            cx, cy = hit.center
            m.mouse().at((cx + offset_x, cy + offset_y)).click().sleep(sleep).perform()
        return OK

    def _event(m: ModuleContext) -> str:
        labels = "/".join(Path(p).name for p in images)
        deadline = time.monotonic() + max(timeout, 0.0)
        last: MatchResult | None = None

        while True:
            for path in images:
                hit = m.find(path, timeout=0.0, **find_kw)
                last = hit
                if hit.found:
                    if len(images) > 1:
                        m.log("命中 [%s]", Path(path).name)
                    return _perform(m, hit)

            if timeout <= 0 or time.monotonic() >= deadline:
                m.value = last
                m.log("未找到 [%s]", labels)
                return MISS
            m.sleep(interval)

    return _event
