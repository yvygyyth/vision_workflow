"""常用事件工厂（模块的 event 字段）。"""

from __future__ import annotations

from pathlib import Path

from vision_workflow.module import MISS, OK, EventFn, ModuleContext


def click(
    image: str,
    *,
    threshold: float = 0.8,
    timeout: float = 3.0,
    sleep: float = 0.2,
    offset_x: int = 0,
    offset_y: int = 0,
    **find_kwargs,
) -> EventFn:
    """找到模板并点击；返回 OK / MISS（须在 Module.on 中声明）。"""

    def _event(m: ModuleContext) -> str:
        hit = m.find(image, threshold=threshold, timeout=timeout, **find_kwargs)
        m.value = hit
        label = Path(image).name
        if not hit.found:
            m.log("未找到 [%s]", label)
            return MISS
        if hit.center:
            cx, cy = hit.center
            point = (cx + int(offset_x), cy + int(offset_y))
            m.mouse().at(point).click().sleep(sleep).perform()
        return OK

    return _event
