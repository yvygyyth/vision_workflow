"""滚轮事件：链式配置，execute() 得到 Module.event。

支持锚点滚轮或识图定位后滚轮::

    scroll().at("center").amount(-8).execute()
    scroll().image("x.png").amount(-8).offset(0, 10).execute()
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from vision_workflow.events.support.anchor import ScrollAnchor, resolve_anchor
from vision_workflow.events.support.find import wait_image
from vision_workflow.module import EventFn, ModuleContext
from vision_workflow.status import FULFILLED, REJECTED, OutcomeKey


@dataclass(frozen=True)
class _Scroll:
    """链式：scroll().at(...)/image(...).amount(...).execute()"""

    wheel: int | None = None
    anchor: ScrollAnchor | None = None
    images: tuple[str, ...] = ()
    offset_x: int = 0
    offset_y: int = 0
    threshold: float = 0.8
    timeout: float = 3.0
    interval: float = 0.5
    sleep: float = 0.3
    region: tuple[int, int, int, int] | None = None
    grayscale: bool | None = None

    def at(self, target: ScrollAnchor) -> _Scroll:
        """在坐标或快捷锚点处滚轮（与 image 二选一）。"""
        return replace(self, anchor=target, images=())

    def image(self, *images: str) -> _Scroll:
        """识图定位后在该点滚轮（与 at 二选一；多图按顺序优先）。"""
        if not images:
            raise ValueError("image() 至少需要一张模板图")
        return replace(self, images=self.images + images, anchor=None)

    def amount(self, value: int) -> _Scroll:
        """滚轮刻度：>0 向上，<0 向下。"""
        return replace(self, wheel=value)

    def offset(self, x: int = 0, y: int = 0) -> _Scroll:
        """相对命中中心 / 锚点的偏移（仅 image 模式常用）。"""
        return replace(self, offset_x=x, offset_y=y)

    def match(
        self,
        *,
        threshold: float | None = None,
        timeout: float | None = None,
        interval: float | None = None,
        region: tuple[int, int, int, int] | None = None,
        grayscale: bool | None = None,
    ) -> _Scroll:
        """识图参数（仅 image 模式）。"""
        return replace(
            self,
            threshold=self.threshold if threshold is None else threshold,
            timeout=self.timeout if timeout is None else timeout,
            interval=self.interval if interval is None else interval,
            region=self.region if region is None else region,
            grayscale=self.grayscale if grayscale is None else grayscale,
        )

    def pause(self, seconds: float) -> _Scroll:
        """滚轮后等待秒数。"""
        return replace(self, sleep=seconds)

    def execute(self) -> EventFn:
        """固化为 Module.event 可调用对象。"""
        if self.wheel is None:
            raise ValueError("scroll 需要先 .amount(...)")
        if self.anchor is None and not self.images:
            raise ValueError("scroll 需要 .at(...) 或 .image(...)")

        amount = self.wheel
        anchor = self.anchor
        images = self.images
        ox, oy = self.offset_x, self.offset_y
        threshold = self.threshold
        timeout = self.timeout
        interval = self.interval
        sleep = self.sleep
        region = self.region
        grayscale = self.grayscale

        def _event(m: ModuleContext) -> OutcomeKey:
            if images:
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
                    return REJECTED
                cx, cy = hit.center
                point = (cx + ox, cy + oy)
            else:
                assert anchor is not None
                ax, ay = resolve_anchor(anchor)
                point = (ax + ox, ay + oy)

            m.log("滚轮 amount=%s @ %s", amount, point)
            m.mouse().at(point).scroll(amount).sleep(sleep).perform()
            return FULFILLED

        return _event


def scroll() -> _Scroll:
    """开始一条滚轮链。"""
    return _Scroll()
