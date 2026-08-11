"""鼠标操作：链式调用。

示例::

    Mouse().move(100, 200).click().sleep(0.3).drag(300, 400).perform()
    Mouse(dry_run=True).at(match.center).click().perform()
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Literal, Self

logger = logging.getLogger(__name__)

Button = Literal["left", "right", "middle"]


@dataclass
class _Op:
    name: str
    kwargs: dict[str, Any]
    runner: Callable[[], None]


@dataclass
class Mouse:
    """链式鼠标控制器。调用 perform()/run() 才真正执行。"""

    dry_run: bool = False
    _ops: list[_Op] = field(default_factory=list, repr=False)
    _x: int | None = field(default=None, repr=False)
    _y: int | None = field(default=None, repr=False)

    def at(self, point: tuple[int, int] | None) -> Self:
        """设置当前基准坐标（通常来自识图中心）。"""
        if point is None:
            raise ValueError("at() 需要有效坐标")
        self._x, self._y = int(point[0]), int(point[1])
        return self

    def move(
        self,
        x: int | None = None,
        y: int | None = None,
        *,
        relative: bool = False,
        duration: float = 0.15,
    ) -> Self:
        """移动到绝对坐标，或相对当前点偏移。"""

        def run() -> None:
            nx, ny = self._resolve_xy(x, y, relative=relative)
            self._x, self._y = nx, ny
            if self.dry_run:
                logger.info("(dry-run) mouse.move → (%s, %s)", nx, ny)
                return
            self._api().moveTo(nx, ny, duration=duration)

        self._ops.append(_Op("move", {"x": x, "y": y, "relative": relative}, run))
        return self

    def click(
        self,
        button: Button = "left",
        clicks: int = 1,
        *,
        x: int | None = None,
        y: int | None = None,
    ) -> Self:
        def run() -> None:
            nx, ny = self._resolve_xy(x, y, relative=False)
            self._x, self._y = nx, ny
            if self.dry_run:
                logger.info("(dry-run) mouse.click %s x%s @ (%s, %s)", button, clicks, nx, ny)
                return
            self._api().click(x=nx, y=ny, clicks=clicks, button=button)

        self._ops.append(_Op("click", {"button": button, "clicks": clicks}, run))
        return self

    def double_click(self, button: Button = "left") -> Self:
        return self.click(button=button, clicks=2)

    def right_click(self) -> Self:
        return self.click(button="right")

    def drag(
        self,
        x: int,
        y: int,
        *,
        relative: bool = False,
        duration: float = 0.3,
        button: Button = "left",
    ) -> Self:
        def run() -> None:
            if self._x is None or self._y is None:
                raise RuntimeError("drag 前需要先有起点坐标（at/move/click）")
            sx, sy = self._x, self._y
            ex, ey = self._resolve_xy(x, y, relative=relative)
            if self.dry_run:
                logger.info("(dry-run) mouse.drag (%s,%s) → (%s,%s)", sx, sy, ex, ey)
                self._x, self._y = ex, ey
                return
            api = self._api()
            api.moveTo(sx, sy)
            api.dragTo(ex, ey, duration=duration, button=button)
            self._x, self._y = ex, ey

        self._ops.append(_Op("drag", {"x": x, "y": y, "relative": relative}, run))
        return self

    def scroll(self, amount: int, *, x: int | None = None, y: int | None = None) -> Self:
        def run() -> None:
            nx, ny = self._resolve_xy(x, y, relative=False)
            if self.dry_run:
                logger.info("(dry-run) mouse.scroll %s @ (%s, %s)", amount, nx, ny)
                return
            self._api().scroll(amount, x=nx, y=ny)

        self._ops.append(_Op("scroll", {"amount": amount}, run))
        return self

    def sleep(self, seconds: float) -> Self:
        def run() -> None:
            if self.dry_run:
                logger.info("(dry-run) mouse.sleep %.3fs", seconds)
                return
            time.sleep(seconds)

        self._ops.append(_Op("sleep", {"seconds": seconds}, run))
        return self

    def perform(self) -> Self:
        """执行队列中的全部操作，并清空队列。"""
        ops, self._ops = self._ops, []
        for op in ops:
            logger.debug("mouse chain: %s %s", op.name, op.kwargs)
            op.runner()
        return self

    # 别名，方便链式末尾书写
    run = perform
    go = perform

    def clear(self) -> Self:
        self._ops.clear()
        return self

    def __len__(self) -> int:
        return len(self._ops)

    def _resolve_xy(
        self,
        x: int | None,
        y: int | None,
        *,
        relative: bool,
    ) -> tuple[int, int]:
        if relative:
            if self._x is None or self._y is None:
                raise RuntimeError("相对坐标需要先设置基准点（at/move/click）")
            return self._x + int(x or 0), self._y + int(y or 0)

        if x is not None and y is not None:
            return int(x), int(y)
        if self._x is not None and self._y is not None:
            return self._x, self._y
        # 回落到当前鼠标位置
        pos = self._api().position()
        return int(pos[0]), int(pos[1])

    @staticmethod
    def _api():
        try:
            import pyautogui
        except ImportError as exc:
            raise RuntimeError("请安装 pyautogui: pip install pyautogui") from exc
        pyautogui.FAILSAFE = True
        return pyautogui
