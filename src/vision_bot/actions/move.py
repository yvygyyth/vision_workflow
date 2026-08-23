"""移动动作。"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Callable, Literal

from vision_bot.actions.anchor import PointAnchor, resolve_anchor
from vision_bot.actions.context import ActionContext
from vision_bot.actions.outcome import ActionOutcome, ActionStatus
from vision_bot.actions.wait import wait_image
from vision_bot.core.display import cached_template_scale
from vision_bot.core.input import Mouse

ActionFn = Callable[[ActionContext], ActionOutcome]
_Mode = Literal["abs", "rel", "image", "anchor"]


def _fit_xy(x: int, y: int, *, fit: bool) -> tuple[int, int]:
    if not fit:
        return int(x), int(y)
    scale = cached_template_scale()
    return int(round(x * scale)), int(round(y * scale))


@dataclass(frozen=True)
class Move:
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

    def to(self, x: int, y: int) -> Move:
        return replace(self, mode="abs", x=x, y=y, images=(), anchor=None)

    def by(self, dx: int, dy: int) -> Move:
        return replace(self, mode="rel", x=dx, y=dy, images=(), anchor=None)

    def image(self, *images: str) -> Move:
        if not images:
            raise ValueError("image() 至少需要一张模板图")
        return replace(self, mode="image", images=self.images + images, anchor=None)

    def at(self, target: PointAnchor) -> Move:
        return replace(self, mode="anchor", anchor=target, images=())

    def match(
        self,
        *,
        threshold: float | None = None,
        timeout: float | None = None,
        interval: float | None = None,
        region: tuple[int, int, int, int] | None = None,
        grayscale: bool | None = None,
    ) -> Move:
        return replace(
            self,
            threshold=self.threshold if threshold is None else threshold,
            timeout=self.timeout if timeout is None else timeout,
            interval=self.interval if interval is None else interval,
            region=self.region if region is None else region,
            grayscale=self.grayscale if grayscale is None else grayscale,
        )

    def speed(self, duration: float) -> Move:
        return replace(self, duration=duration)

    def pause(self, seconds: float) -> Move:
        return replace(self, sleep=seconds)

    def raw(self) -> Move:
        return replace(self, fit_display=False)

    def execute(self) -> ActionFn:
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

        def _run(ctx: ActionContext) -> ActionOutcome:
            mouse = Mouse()
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
                    ctx,
                    images,
                    threshold=threshold,
                    timeout=timeout,
                    interval=interval,
                    region=region,
                    grayscale=grayscale,
                )
                if hit is None or not hit.center:
                    if not ctx.reason:
                        ctx.reason = "识图未命中" if hit is None else "识图命中但无中心点"
                    return ActionOutcome(ActionStatus.FAIL, reason=ctx.reason)
                cx, cy = hit.center
                mouse.move(cx, cy, duration=duration)

            if sleep > 0:
                mouse.sleep(sleep)
            mouse.perform()
            return ActionOutcome(ActionStatus.OK)

        return _run


def move() -> Move:
    return Move()
