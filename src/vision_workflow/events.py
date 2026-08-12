"""常用事件工厂（模块的 event 字段）。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from vision_workflow.flow.context import FlowContext
from vision_workflow.module import EventFn
from vision_workflow.promise import Settled


def click(
    image: str,
    *,
    threshold: float = 0.8,
    timeout: float = 3.0,
    sleep: float = 0.2,
    offset_x: int = 0,
    offset_y: int = 0,
    **find_kwargs: Any,
) -> EventFn:
    """找到模板并点击；默认点中心，可用 offset_x / offset_y 相对偏移。"""

    def _event(ctx: FlowContext) -> Any:
        hit = ctx.find(image, threshold=threshold, timeout=timeout, **find_kwargs)
        label = Path(image).name
        if not hit.found:
            return Settled.reject(hit.message, value=hit, feedback=f"未找到 [{label}]")
        if hit.center:
            cx, cy = hit.center
            point = (cx + int(offset_x), cy + int(offset_y))
            ctx.mouse().at(point).click().sleep(sleep).perform()
        return hit

    return _event
