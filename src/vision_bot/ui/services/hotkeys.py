"""全局快捷键。"""

from __future__ import annotations

import logging
from collections.abc import Callable

logger = logging.getLogger(__name__)

TOGGLE_HOTKEY = "<f9>"
TOGGLE_LABEL = "F9"


class GlobalHotkeys:
    def __init__(
        self,
        *,
        on_toggle: Callable[[], None],
        schedule: Callable[[Callable[[], None]], None],
    ) -> None:
        self._on_toggle = on_toggle
        self._schedule = schedule
        self._listener = None

    def start(self) -> None:
        if self._listener is not None:
            return
        try:
            from pynput import keyboard
        except ImportError as exc:
            logger.warning("未安装 pynput: %s", exc)
            return

        self._listener = keyboard.GlobalHotKeys({TOGGLE_HOTKEY: lambda: self._schedule(self._on_toggle)})
        self._listener.start()

    def stop(self) -> None:
        if self._listener:
            self._listener.stop()
            self._listener = None
