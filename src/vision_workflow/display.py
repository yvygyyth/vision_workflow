"""当前设备显示参数（供跨分辨率识图缩放等使用）。"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class DisplayInfo:
    """截图 / DPI 相关快照。"""

    screen_width: int
    screen_height: int
    screenshot_width: int
    screenshot_height: int
    virtual_width: int
    virtual_height: int
    dpi: int
    scale_percent: float
    """相对 96 DPI 的缩放百分比，如 125.0。"""

    @property
    def screen_size(self) -> tuple[int, int]:
        return self.screen_width, self.screen_height

    @property
    def screenshot_size(self) -> tuple[int, int]:
        return self.screenshot_width, self.screenshot_height

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def get_display_info() -> DisplayInfo:
    """读取本机当前显示参数（Windows 下尽量用真实像素 + 有效 DPI）。"""
    _ensure_dpi_aware()

    screen_w, screen_h = _screen_size()
    shot_w, shot_h = _screenshot_size()
    virt_w, virt_h = _virtual_screen_size()
    dpi = _effective_dpi()
    scale = round(dpi / 96.0 * 100.0, 1)

    return DisplayInfo(
        screen_width=screen_w,
        screen_height=screen_h,
        screenshot_width=shot_w,
        screenshot_height=shot_h,
        virtual_width=virt_w,
        virtual_height=virt_h,
        dpi=dpi,
        scale_percent=scale,
    )


def _ensure_dpi_aware() -> None:
    try:
        import ctypes

        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass
    except Exception:
        pass


def _screen_size() -> tuple[int, int]:
    try:
        import pyautogui

        size = pyautogui.size()
        return int(size[0]), int(size[1])
    except Exception:
        pass
    try:
        import ctypes

        user32 = ctypes.windll.user32
        return int(user32.GetSystemMetrics(0)), int(user32.GetSystemMetrics(1))
    except Exception:
        return 0, 0


def _virtual_screen_size() -> tuple[int, int]:
    try:
        import ctypes

        user32 = ctypes.windll.user32
        # SM_CXVIRTUALSCREEN / SM_CYVIRTUALSCREEN
        return int(user32.GetSystemMetrics(78)), int(user32.GetSystemMetrics(79))
    except Exception:
        return _screen_size()


def _screenshot_size() -> tuple[int, int]:
    try:
        from PIL import ImageGrab

        im = ImageGrab.grab()
        return int(im.size[0]), int(im.size[1])
    except Exception:
        return _screen_size()


def _effective_dpi() -> int:
    try:
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.windll.user32
        shcore = ctypes.windll.shcore
        mon = user32.MonitorFromPoint(wintypes.POINT(0, 0), 1)
        dpi_x = ctypes.c_uint()
        dpi_y = ctypes.c_uint()
        # MDT_EFFECTIVE_DPI = 0
        shcore.GetDpiForMonitor(mon, 0, ctypes.byref(dpi_x), ctypes.byref(dpi_y))
        return int(dpi_x.value or 96)
    except Exception:
        pass
    try:
        import ctypes

        return int(ctypes.windll.user32.GetDpiForSystem() or 96)
    except Exception:
        return 96
