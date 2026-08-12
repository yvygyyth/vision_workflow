"""常用事件工厂（供 Module.event 使用）。"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Literal

from vision_workflow.models.flow import MatchResult
from vision_workflow.module import MISS, OK, EventFn, ModuleContext

# 滚轮锚点：绝对坐标，或快捷名
ScrollAnchor = tuple[int, int] | Literal["center"]


def _screen_center() -> tuple[int, int]:
    try:
        import pyautogui
    except ImportError as exc:
        raise RuntimeError("请安装 pyautogui: pip install pyautogui") from exc
    w, h = pyautogui.size()
    return w // 2, h // 2


def resolve_anchor(target: ScrollAnchor) -> tuple[int, int]:
    """将坐标或快捷名解析为屏幕像素点。"""
    if isinstance(target, tuple) and len(target) == 2:
        return int(target[0]), int(target[1])
    if target == "center":
        return _screen_center()
    raise ValueError(f"不支持的锚点: {target!r}（可用 (x, y) 或 'center'）")


def _find_kw(
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


def _wait_image(
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
    find_kw = _find_kw(threshold=threshold, region=region, grayscale=grayscale)
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
                m.value = hit
                return hit
        if timeout <= 0 or time.monotonic() >= deadline:
            m.value = last
            m.log("未找到 [%s]", labels)
            return None
        m.sleep(interval)


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
    """
    if not images:
        raise ValueError("click_image() 至少需要一张模板图")

    def _event(m: ModuleContext) -> str:
        hit = _wait_image(
            m,
            images,
            threshold=threshold,
            timeout=timeout,
            interval=interval,
            region=region,
            grayscale=grayscale,
        )
        if hit is None or not hit.center:
            return MISS
        cx, cy = hit.center
        m.mouse().at((cx + offset_x, cy + offset_y)).click().sleep(sleep).perform()
        return OK

    return _event


def scroll_at(
    target: ScrollAnchor = "center",
    *,
    amount: int,
    sleep: float = 0.3,
) -> EventFn:
    """在坐标或快捷锚点处滚轮，返回 OK。

    ``amount`` >0 向上，<0 向下（pyautogui 滚轮刻度）。
    ``target``: ``(x, y)`` 或 ``"center"``（屏幕正中）。
    """

    def _event(m: ModuleContext) -> str:
        point = resolve_anchor(target)
        m.log("滚轮 amount=%s @ %s", amount, point)
        m.mouse().at(point).scroll(amount).sleep(sleep).perform()
        return OK

    return _event


def scroll_image(
    *images: str,
    amount: int,
    threshold: float = 0.8,
    timeout: float = 3.0,
    interval: float = 0.5,
    sleep: float = 0.3,
    offset_x: int = 0,
    offset_y: int = 0,
    region: tuple[int, int, int, int] | None = None,
    grayscale: bool | None = None,
) -> EventFn:
    """识图定位后在该点滚轮，返回 OK / MISS。

    多图按参数顺序优先；``amount`` 同 ``scroll_at``。
    """
    if not images:
        raise ValueError("scroll_image() 至少需要一张模板图")

    def _event(m: ModuleContext) -> str:
        hit = _wait_image(
            m,
            images,
            threshold=threshold,
            timeout=timeout,
            interval=interval,
            region=region,
            grayscale=grayscale,
        )
        if hit is None or not hit.center:
            return MISS
        cx, cy = hit.center
        point = (cx + offset_x, cy + offset_y)
        m.log("滚轮 amount=%s @ %s", amount, point)
        m.mouse().at(point).scroll(amount).sleep(sleep).perform()
        return OK

    return _event
