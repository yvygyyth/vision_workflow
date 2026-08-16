"""移动事件：绝对 / 相对 / 识图 / 锚点。只移动，不点击。"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Literal

from vision_workflow.display import cached_template_scale
from vision_workflow.events.support.anchor import PointAnchor, resolve_anchor
from vision_workflow.events.support.find import wait_image
from vision_workflow.module import EventFn, ModuleContext
from vision_workflow.status import FULFILLED, REJECTED, OutcomeKey

_Mode = Literal["abs", "rel", "image", "anchor"]


def _fit_xy(x: int, y: int, *, fit: bool) -> tuple[int, int]:
    """相对模板基准缩放坐标；fit=False 时原样返回。"""
    if not fit:
        return int(x), int(y)
    scale = cached_template_scale()
    return int(round(x * scale)), int(round(y * scale))


@dataclass(frozen=True)
class _Move:
    mode: _Mode | None = None
    x: int = 0
    y: int = 0
    images: tuple[str, ...] = ()
    anchor: PointAnchor | None = None
    threshold: float = 0.8
    timeout: float = 3.0
    interval: float = 0.5
    region: tuple[int, int, int, int] | None = None
    grayscale: bool | None = None
    duration: float = 0.15
    sleep: float = 0.0
    fit_display: bool = True
    """绝对/相对/(x,y)锚点是否按显示基准缩放；识图命中与 center 不受影响。"""

    def to(self, x: int, y: int) -> _Move:
        """绝对坐标（默认按分辨率相对基准缩放）。"""
        return replace(self, mode="abs", x=x, y=y, images=(), anchor=None)

    def by(self, dx: int, dy: int) -> _Move:
        """相对当前位置偏移（默认按分辨率相对基准缩放）。"""
        return replace(self, mode="rel", x=dx, y=dy, images=(), anchor=None)

    def image(self, *images: str) -> _Move:
        """识图移动到命中中心（多图按顺序优先）。"""
        if not images:
            raise ValueError("image() 至少需要一张模板图")
        return replace(self, mode="image", images=self.images + images, anchor=None)

    def at(self, target: PointAnchor) -> _Move:
        """锚点：``\"center\"`` 或 ``(x, y)``（元组默认缩放，center 不缩放）。"""
        return replace(self, mode="anchor", anchor=target, images=())

    def match(
        self,
        *,
        threshold: float | None = None,
        timeout: float | None = None,
        interval: float | None = None,
        region: tuple[int, int, int, int] | None = None,
        grayscale: bool | None = None,
    ) -> _Move:
        """识图参数（仅 image 模式）。"""
        return replace(
            self,
            threshold=self.threshold if threshold is None else threshold,
            timeout=self.timeout if timeout is None else timeout,
            interval=self.interval if interval is None else interval,
            region=self.region if region is None else region,
            grayscale=self.grayscale if grayscale is None else grayscale,
        )

    def speed(self, duration: float) -> _Move:
        """移动耗时（秒）。"""
        return replace(self, duration=duration)

    def pause(self, seconds: float) -> _Move:
        """移动后等待。"""
        return replace(self, sleep=seconds)

    def raw(self) -> _Move:
        """关闭显示缩放，按字面像素移动（to / by / (x,y) 锚点）。"""
        return replace(self, fit_display=False)

    def fit(self) -> _Move:
        """开启显示缩放（默认已开启；用于取消 .raw()）。"""
        return replace(self, fit_display=True)

    def execute(self) -> EventFn:
        if self.mode is None:
            raise ValueError("move 需要 .to() / .by() / .image() / .at()")

        mode = self.mode
        x, y = self.x, self.y
        images = self.images
        anchor = self.anchor
        threshold = self.threshold
        timeout = self.timeout
        interval = self.interval
        region = self.region
        grayscale = self.grayscale
        duration = self.duration
        sleep = self.sleep
        fit = self.fit_display

        def _event(m: ModuleContext) -> OutcomeKey:
            mouse = m.mouse()
            if mode == "abs":
                sx, sy = _fit_xy(x, y, fit=fit)
                mouse.move(sx, sy, duration=duration)
            elif mode == "rel":
                sx, sy = _fit_xy(x, y, fit=fit)
                mouse.move(sx, sy, relative=True, duration=duration)
            elif mode == "anchor":
                assert anchor is not None
                if isinstance(anchor, tuple):
                    ax, ay = _fit_xy(int(anchor[0]), int(anchor[1]), fit=fit)
                else:
                    ax, ay = resolve_anchor(anchor)
                mouse.move(ax, ay, duration=duration)
            else:
                hit = wait_image(
                    m,
                    images,
                    threshold=threshold,
                    timeout=timeout,
                    interval=interval,
                    region=region,
                    grayscale=grayscale,
                )
                if hit is None or not hit.center:
                    if not m.reason:
                        m.reason = "识图未命中" if hit is None else "识图命中但无中心点"
                    return REJECTED
                cx, cy = hit.center
                mouse.move(cx, cy, duration=duration)

            if sleep > 0:
                mouse.sleep(sleep)
            mouse.perform()
            return FULFILLED

        return _event


def move() -> _Move:
    """开始一条移动链。"""
    return _Move()
