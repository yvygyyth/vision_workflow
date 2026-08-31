"""鼠标 / 键盘操作。

移动与点击分离：先 move/at，再 click/scroll（不带坐标）。

``Mouse.click`` 默认按下后停 ``DEFAULT_CLICK_HOLD_SEC``（50ms）再抬起，
避免部分游戏把瞬时 click 当成只按不放。

示例::

    Mouse().move(100, 200).click().sleep(0.3).perform()
    Mouse().at(match.center).click().perform()
    Mouse().at((960, 540)).scroll(-8).perform()
    press_key("esc")
    input_text("hello")
    input_text("张飞")  # 非 ASCII 自动走剪贴板粘贴
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Literal, Self

logger = logging.getLogger(__name__)

Button = Literal["left", "right", "middle"]

# 按下到抬起的默认间隔；部分游戏对瞬时 click 会当成只按不放
DEFAULT_CLICK_HOLD_SEC = 0.05


def press_key(key: str) -> None:
    """按下并松开一个键（如 esc、enter、space）。"""
    api = _pyautogui()
    logger.debug("key press: %s", key)
    api.press(key)


def hotkey(*keys: str) -> None:
    """组合键，如 ``hotkey("ctrl", "a")``。"""
    if not keys:
        raise ValueError("hotkey 至少需要一个键")
    api = _pyautogui()
    logger.debug("hotkey: %s", "+".join(keys))
    api.hotkey(*keys)


def input_text(
    text: str,
    *,
    interval: float = 0.0,
    method: Literal["auto", "write", "paste"] = "auto",
) -> None:
    """输入字符串。

    - ``write``：逐键敲击（适合 ASCII）
    - ``paste``：剪贴板 + Ctrl+V（适合中文等）
    - ``auto``：纯 ASCII 用 write，否则 paste
    """
    if text == "":
        return
    mode = method
    if mode == "auto":
        mode = "write" if text.isascii() else "paste"
    logger.debug("input_text method=%s len=%s", mode, len(text))
    if mode == "write":
        _pyautogui().write(text, interval=interval)
        return
    if mode == "paste":
        _paste_via_clipboard(text)
        return
    raise ValueError(f"未知 input_text method: {method!r}")


def _paste_via_clipboard(text: str) -> None:
    """Win32 写剪贴板后 Ctrl+V（避免 tkinter 抢焦点导致游戏卡住）。"""
    _set_clipboard_text(text)
    time.sleep(0.05)
    _pyautogui().hotkey("ctrl", "v")


def _set_clipboard_text(text: str) -> None:
    """用 Win32 API 写入 Unicode 文本到剪贴板，不创建窗口。"""
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32

    CF_UNICODETEXT = 13
    GMEM_MOVEABLE = 0x0002

    kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
    kernel32.GlobalAlloc.restype = wintypes.HGLOBAL
    kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalLock.restype = ctypes.c_void_p
    kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalFree.argtypes = [wintypes.HGLOBAL]
    user32.OpenClipboard.argtypes = [wintypes.HWND]
    user32.OpenClipboard.restype = wintypes.BOOL
    user32.EmptyClipboard.restype = wintypes.BOOL
    user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
    user32.SetClipboardData.restype = wintypes.HANDLE
    user32.CloseClipboard.restype = wintypes.BOOL

    data = text.encode("utf-16-le") + b"\x00\x00"
    if not user32.OpenClipboard(None):
        raise RuntimeError(f"OpenClipboard 失败 err={ctypes.get_last_error()}")
    try:
        user32.EmptyClipboard()
        handle = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(data))
        if not handle:
            raise RuntimeError("GlobalAlloc 失败")
        locked = kernel32.GlobalLock(handle)
        if not locked:
            kernel32.GlobalFree(handle)
            raise RuntimeError(f"GlobalLock 失败 err={ctypes.get_last_error()}")
        ctypes.memmove(locked, data, len(data))
        kernel32.GlobalUnlock(handle)
        if not user32.SetClipboardData(CF_UNICODETEXT, handle):
            kernel32.GlobalFree(handle)
            raise RuntimeError(f"SetClipboardData 失败 err={ctypes.get_last_error()}")
    finally:
        user32.CloseClipboard()


def _pyautogui():
    try:
        import pyautogui
    except ImportError as exc:
        raise RuntimeError("请安装 pyautogui: pip install pyautogui") from exc
    pyautogui.FAILSAFE = True
    return pyautogui


class CursorKind(str, Enum):
    """系统光标形态（Win32 标准光标；类比 CSS cursor）。"""

    HIDDEN = "hidden"
    ARROW = "arrow"
    HAND = "hand"  # 约等于 CSS pointer
    IBEAM = "ibeam"
    WAIT = "wait"
    OTHER = "other"


@dataclass(frozen=True, slots=True)
class CursorState:
    """当前系统光标快照。"""

    kind: CursorKind
    visible: bool
    x: int
    y: int

    @property
    def is_pointer(self) -> bool:
        """是否为可点击手型（``IDC_HAND`` / CSS ``pointer``）。"""
        return self.kind == CursorKind.HAND

    @property
    def is_hidden(self) -> bool:
        """系统光标是否不可见。"""
        return not self.visible or self.kind == CursorKind.HIDDEN


def get_cursor_state() -> CursorState:
    """读取 Windows 系统光标状态（非游戏自绘准星）。

    通过 ``GetCursorInfo`` 判断是否显示，并与标准光标句柄比对形态。
    非 Windows 平台返回 ``OTHER`` 且 ``visible=True``。
    """
    import sys

    if sys.platform != "win32":
        pos = _pyautogui().position()
        return CursorState(
            kind=CursorKind.OTHER,
            visible=True,
            x=int(pos[0]),
            y=int(pos[1]),
        )

    import ctypes
    from ctypes import wintypes

    class CURSORINFO(ctypes.Structure):
        _fields_ = [
            ("cbSize", wintypes.DWORD),
            ("flags", wintypes.DWORD),
            ("hCursor", wintypes.HANDLE),
            ("ptScreenPos", wintypes.POINT),
        ]

    user32 = ctypes.windll.user32
    CURSOR_SHOWING = 0x00000001
    # https://learn.microsoft.com/windows/win32/menurc/about-cursors
    _STD = {
        CursorKind.ARROW: 32512,  # IDC_ARROW
        CursorKind.IBEAM: 32513,  # IDC_IBEAM
        CursorKind.WAIT: 32514,  # IDC_WAIT
        CursorKind.HAND: 32649,  # IDC_HAND
    }

    info = CURSORINFO()
    info.cbSize = ctypes.sizeof(CURSORINFO)
    if not user32.GetCursorInfo(ctypes.byref(info)):
        pos = _pyautogui().position()
        return CursorState(
            kind=CursorKind.OTHER,
            visible=True,
            x=int(pos[0]),
            y=int(pos[1]),
        )

    visible = bool(info.flags & CURSOR_SHOWING)
    x, y = int(info.ptScreenPos.x), int(info.ptScreenPos.y)
    if not visible:
        return CursorState(kind=CursorKind.HIDDEN, visible=False, x=x, y=y)

    handle = int(info.hCursor) if info.hCursor else 0
    for kind, res_id in _STD.items():
        std = int(user32.LoadCursorW(None, res_id) or 0)
        if std and handle == std:
            return CursorState(kind=kind, visible=True, x=x, y=y)
    return CursorState(kind=CursorKind.OTHER, visible=True, x=x, y=y)


def cursor_is_pointer() -> bool:
    """当前系统光标是否为手型（可点击）。"""
    return get_cursor_state().is_pointer


def cursor_is_hidden() -> bool:
    """当前系统光标是否隐藏。"""
    return get_cursor_state().is_hidden


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

    def down(self, button: Button = "left") -> Self:
        """按下鼠标键（不抬起）。"""

        def run() -> None:
            self._api().mouseDown(button=button)

        self._ops.append(_Op("down", {"button": button}, run))
        return self

    def up(self, button: Button = "left") -> Self:
        """抬起鼠标键。"""

        def run() -> None:
            self._api().mouseUp(button=button)

        self._ops.append(_Op("up", {"button": button}, run))
        return self

    def click(
        self,
        button: Button = "left",
        clicks: int = 1,
        *,
        hold: float = DEFAULT_CLICK_HOLD_SEC,
    ) -> Self:
        """在当前位置点击（按下→短停→抬起）。需先 move/at，或接受当前系统光标位置。"""

        def run() -> None:
            api = self._api()
            for _ in range(max(1, clicks)):
                api.mouseDown(button=button)
                if hold > 0:
                    time.sleep(hold)
                api.mouseUp(button=button)
            pos = api.position()
            self._x, self._y = int(pos[0]), int(pos[1])

        self._ops.append(
            _Op("click", {"button": button, "clicks": clicks, "hold": hold}, run)
        )
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
                # do(move().image(), move().by()) 会新建 Mouse 链；退回当前光标
                pos = self._api().position()
                self._x, self._y = int(pos[0]), int(pos[1])
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
