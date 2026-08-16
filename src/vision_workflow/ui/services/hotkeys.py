"""全局快捷键（游戏前台也可触发）。"""

from __future__ import annotations

import logging
from collections.abc import Callable

logger = logging.getLogger(__name__)

# 默认：F9 切换运行 / 停止
TOGGLE_HOTKEY = "<f9>"
TOGGLE_LABEL = "F9"


class GlobalHotkeys:
    """用 pynput 注册全局热键；回调经 schedule 丢回 UI 线程。"""

    def __init__(
        self,
        *,
        on_toggle: Callable[[], None],
        schedule: Callable[[Callable[[], None]], None],
        toggle_hotkey: str = TOGGLE_HOTKEY,
    ) -> None:
        self._on_toggle = on_toggle
        self._schedule = schedule
        self._toggle_hotkey = toggle_hotkey
        self._listener = None

    def start(self) -> None:
        if self._listener is not None:
            return
        try:
            from pynput import keyboard
        except ImportError as exc:
            logger.warning("未安装 pynput，全局快捷键不可用: %s", exc)
            return

        def _fire() -> None:
            self._schedule(self._on_toggle)

        self._listener = keyboard.GlobalHotKeys({self._toggle_hotkey: _fire})
        self._listener.start()
        logger.info("全局快捷键已启用 %s = 运行/停止", TOGGLE_LABEL)

    def stop(self) -> None:
        listener = self._listener
        self._listener = None
        if listener is None:
            return
        try:
            listener.stop()
        except Exception:  # noqa: BLE001
            logger.exception("停止全局快捷键失败")
