"""识图点击事件：链式配置，execute() 得到 Module.event。"""

from __future__ import annotations

from dataclasses import dataclass, replace

from vision_workflow.events.support.find import wait_image
from vision_workflow.module import EventFn, ModuleContext
from vision_workflow.status import FULFILLED, REJECTED, OutcomeKey


@dataclass(frozen=True)
class Click:
    """链式：click().image(...).offset(...).execute()"""

    images: tuple[str, ...] = ()
    offset_x: int = 0
    offset_y: int = 0
    threshold: float = 0.8
    timeout: float = 3.0
    interval: float = 0.5
    sleep: float = 0.2
    region: tuple[int, int, int, int] | None = None
    grayscale: bool | None = None

    def image(self, *images: str) -> Click:
        """追加模板图（多张按参数顺序优先匹配）。"""
        if not images:
            raise ValueError("image() 至少需要一张模板图")
        return replace(self, images=self.images + images)

    def offset(self, x: int = 0, y: int = 0) -> Click:
        """相对命中中心的点击偏移。"""
        return replace(self, offset_x=x, offset_y=y)

    def match(
        self,
        *,
        threshold: float | None = None,
        timeout: float | None = None,
        interval: float | None = None,
        region: tuple[int, int, int, int] | None = None,
        grayscale: bool | None = None,
    ) -> Click:
        """识图参数。"""
        return replace(
            self,
            threshold=self.threshold if threshold is None else threshold,
            timeout=self.timeout if timeout is None else timeout,
            interval=self.interval if interval is None else interval,
            region=self.region if region is None else region,
            grayscale=self.grayscale if grayscale is None else grayscale,
        )

    def pause(self, seconds: float) -> Click:
        """点击后等待秒数。"""
        return replace(self, sleep=seconds)

    def execute(self) -> EventFn:
        """固化为 Module.event 可调用对象。"""
        if not self.images:
            raise ValueError("click 需要先 .image(...) 指定模板")

        images = self.images
        ox, oy = self.offset_x, self.offset_y
        threshold = self.threshold
        timeout = self.timeout
        interval = self.interval
        sleep = self.sleep
        region = self.region
        grayscale = self.grayscale

        def _event(m: ModuleContext) -> OutcomeKey:
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
            m.mouse().at((cx + ox, cy + oy)).click().sleep(sleep).perform()
            return FULFILLED

        return _event


def click() -> Click:
    """开始一条识图点击链。"""
    return Click()
