"""千里单骑 · 休息动作。"""

from __future__ import annotations

import logging
import random

from vision_workflow.events import click, do, move
from vision_workflow.module import ModuleContext
from vision_workflow.status import FULFILLED, OutcomeKey

logger = logging.getLogger(__name__)

# 相对模板基准的绝对坐标（move.to 会 fit）
REST_POINTS: tuple[tuple[int, int], ...] = (
    (110, 1100),
    (960, 1100),
    (1800, 1100),
)


def click_rest_slot(m: ModuleContext) -> OutcomeKey:
    """随机点三个休息槽位之一。"""
    x, y = random.choice(REST_POINTS)
    logger.info("click_rest_slot @ (%s,%s)", x, y)
    m.reason = f"休息点 ({x},{y})"
    key = do(move().to(x, y).raw(), click())(m)
    return key if key is not None else FULFILLED
