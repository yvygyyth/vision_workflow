"""事件共享：滚轮锚点。"""

from __future__ import annotations

from typing import Literal

ScrollAnchor = tuple[int, int] | Literal["center"]


def screen_center() -> tuple[int, int]:
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
        return screen_center()
    raise ValueError(f"不支持的锚点: {target!r}（可用 (x, y) 或 'center'）")
