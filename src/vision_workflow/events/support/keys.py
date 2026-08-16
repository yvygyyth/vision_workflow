"""按 Esc 的共享实现。"""

from __future__ import annotations

import logging
import time

from vision_workflow.input import press_key
from vision_workflow.module import EventFn, ModuleContext
from vision_workflow.status import FULFILLED, OutcomeKey

logger = logging.getLogger(__name__)


def press_esc_event(label: str, *, pause: float = 0.2) -> EventFn:
    """发送 Esc 并可选等待；label 仅用于日志。"""

    def _event(_m: ModuleContext) -> OutcomeKey:
        logger.info("%s: Esc", label)
        press_key("esc")
        if pause > 0:
            time.sleep(pause)
        return FULFILLED

    return _event
