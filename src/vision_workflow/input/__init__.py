"""鼠标 / 键盘操作。

移动与点击分离：先 move/at，再 click/scroll（不带坐标）。

示例::

    Mouse().move(100, 200).click().sleep(0.3).perform()
    Mouse().at(match.center).click().perform()
    Mouse().at((960, 540)).scroll(-8).perform()
    press_key("esc")
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Literal, Self

logger = logging.getLogger(__name__)

Button = Literal["left", "right", "middle"]


def press_key(key: str) -> None:
    """按下并松开一个键（如 esc、enter、space）。"""
    api = _pyautogui()
    logger.debug("key press: %s", key)
    api.press(key)


def _pyautogui():
    try:
        import pyautogui
    except ImportError as exc:
        raise RuntimeError("请安装 pyautogui: pip install pyautogui") from exc
    pyautogui.FAILSAFE = True
    return pyautogui


@dataclass
class _Op:
    name: str
    kwargs: dict[str, Any]
    runner: Callable[[], None]


@dataclass
class Mouse:
    """链式鼠标控制器。调用 perform()/run() 才真正执行。"""

    _ops: list[_Op] = field(default_factory=list, repr=False)
    _x: int | None = field(default=None, repr=False)
    _y: int | None = field(default=None, repr=False)

    def at(self, point: tuple[int, int] | None) -> Self:
        """移动到坐标（只 move）。"""
        if point is None:
            raise ValueError("at() 需要有效坐标")
        return self.move(int(point[0]), int(point[1]))

    def move(
        self,
        x: int | None = None,
        y: int | None = None,
        *,
        relative: bool = False,
        duration: float = 0.15,
    ) -> Self:
        """移动到绝对坐标，或相对当前点偏移。不点击。"""

        def run() -> None:
            nx, ny = self._resolve_xy(x, y, relative=relative)
            self._x, self._y = nx, ny
            self._api().moveTo(nx, ny, duration=duration)

        self._ops.append(_Op("move", {"x": x, "y": y, "relative": relative}, run))
        return self

    def click(self, button: Button = "left", clicks: int = 1) -> Self:
        """在当前位置点击（不移动）。需先 move/at，或接受当前系统光标位置。"""

        def run() -> None:
            api = self._api()
            api.click(clicks=clicks, button=button)
            pos = api.position()
            self._x, self._y = int(pos[0]), int(pos[1])

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
        """从当前位置拖到目标（起点需已 move/at）。"""

        def run() -> None:
            if self._x is None or self._y is None:
                raise RuntimeError("drag 前需要先 move/at 到起点")
            sx, sy = self._x, self._y
            ex, ey = self._resolve_xy(x, y, relative=relative)
            api = self._api()
            api.moveTo(sx, sy)
            api.dragTo(ex, ey, duration=duration, button=button)
            self._x, self._y = ex, ey

        self._ops.append(_Op("drag", {"x": x, "y": y, "relative": relative}, run))
        return self

    def scroll(self, amount: int) -> Self:
        """在当前位置滚轮（不移动）。需先 move/at，或接受当前系统光标位置。"""

        def run() -> None:
            self._api().scroll(amount)

        self._ops.append(_Op("scroll", {"amount": amount}, run))
        return self

    def sleep(self, seconds: float) -> Self:
        def run() -> None:
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
                raise RuntimeError("相对坐标需要先设置基准点（at/move）")
            return self._x + int(x or 0), self._y + int(y or 0)

        if x is not None and y is not None:
            return int(x), int(y)
        if self._x is not None and self._y is not None:
            return self._x, self._y
        pos = self._api().position()
        return int(pos[0]), int(pos[1])

    @staticmethod
    def _api():
        return _pyautogui()
