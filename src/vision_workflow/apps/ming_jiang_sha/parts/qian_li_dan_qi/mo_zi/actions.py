"""千里单骑 · 墨子事件动作。"""

from __future__ import annotations

import logging
import random

from vision_workflow.events import click, do, move
from vision_workflow.module import ModuleContext
from vision_workflow.status import FULFILLED, OutcomeKey

logger = logging.getLogger(__name__)

OPTION_POINTS: tuple[tuple[int, int], ...] = (
    (1130, 360),
    (1130, 630),
    (1130, 900),
)


def click_option(m: ModuleContext) -> OutcomeKey:
    """随机点三个选项坐标之一。"""
    x, y = random.choice(OPTION_POINTS)
    logger.info("mo_zi click_option @ (%s,%s)", x, y)
    m.reason = f"墨子选项 ({x},{y})"
    key = do(move().to(x, y).raw(), click())(m)
    return key if key is not None else FULFILLED
