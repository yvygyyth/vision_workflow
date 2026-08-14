"""当前设备显示参数与模板基准（跨分辨率识图缩放）。"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from functools import lru_cache
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

    def format_line(self, *, prefix: str = "显示参数") -> str:
        return (
            f"{prefix} screen={self.screen_width}x{self.screen_height} "
            f"shot={self.screenshot_width}x{self.screenshot_height} "
            f"dpi={self.dpi} scale={self.scale_percent:g}% "
            f"virtual={self.virtual_width}x{self.virtual_height}"
        )


# 识图默认（min/max/samples/baseline）统一在 settings.MatchSettings，勿在此再维护一份


def active_baseline() -> DisplayInfo:
    """当前生效的模板基准（来自设置；基准宽高以 MatchSettings 代码默认为准）。"""
    from vision_workflow.settings import get_match_settings

    s = get_match_settings()
    w, h = s.baseline_width, s.baseline_height
    return DisplayInfo(
        screen_width=w,
        screen_height=h,
        screenshot_width=w,
        screenshot_height=h,
        virtual_width=w,
        virtual_height=h,
        dpi=96,
        scale_percent=100.0,
    )


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


def template_scale(
    current: DisplayInfo | None = None,
    *,
    baseline: DisplayInfo | None = None,
) -> float:
    """当前设备相对模板基准的识图缩放比。

    以截图像素为主（已含系统缩放对抓屏的影响），再乘 DPI/缩放比作补充。
    """
    cur = current or get_display_info()
    base = baseline or active_baseline()
    if base.screenshot_width <= 0 or base.screenshot_height <= 0:
        return 1.0

    sx = cur.screenshot_width / base.screenshot_width
    sy = cur.screenshot_height / base.screenshot_height
    size_scale = math.sqrt(max(sx, 1e-9) * max(sy, 1e-9))

    dpi_scale = 1.0
    if base.scale_percent > 0:
        dpi_scale = cur.scale_percent / base.scale_percent

    # 截图像素已反映物理像素时，dpi_scale≈1；若逻辑分辨率相同但缩放不同，dpi 仍能拉开差距
    # 为避免双重放大：仅当截图宽高比与基准几乎一致且尺寸接近时，更信任 size；差距大时用 size
    if abs(sx - 1.0) < 0.02 and abs(sy - 1.0) < 0.02 and abs(dpi_scale - 1.0) > 0.02:
        return float(dpi_scale)
    return float(size_scale)


@lru_cache(maxsize=1)
def cached_template_scale() -> float:
    """进程内缓存一次；分辨率中途变更需清缓存。"""
    return template_scale()


def match_scales(base: float | None = None) -> list[float]:
    """多尺度列表；关闭 multi_scale 时只返回基准换算 scale。"""
    from vision_workflow.settings import get_match_settings

    center = cached_template_scale() if base is None else float(base)
    cfg = get_match_settings()
    if not cfg.multi_scale:
        return [center]

    lo = center * float(cfg.scale_min)
    hi = center * float(cfg.scale_max)
    if hi < lo:
        lo, hi = hi, lo
    n = max(2, int(cfg.scale_samples))
    if abs(hi - lo) < 1e-9:
        return [center]
    return [lo + (hi - lo) * i / (n - 1) for i in range(n)]


def clear_display_cache() -> None:
    cached_template_scale.cache_clear()


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
