"""千里单骑 · 妃妃事件动作。"""

from __future__ import annotations

import logging

from vision_workflow.apps.ming_jiang_sha.common.paths import DATA_ROOT
from vision_workflow.events import click, do, move
from vision_workflow.module import ModuleContext
from vision_workflow.status import FULFILLED, REJECTED, OutcomeKey

logger = logging.getLogger(__name__)

_DIR = f"{DATA_ROOT}/qian_li_dan_qi/fei_fei"

# 选项优先级：我来帮你 → 快睡午觉 → 讨价还价
_OPTION_PRIORITY: tuple[tuple[str, str], ...] = (
    (f"{_DIR}/i_help_you.png", "我来帮你"),
    (f"{_DIR}/sleep.png", "快睡午觉"),
    (f"{_DIR}/bargaining.png", "讨价还价"),
)


def choose_option(m: ModuleContext) -> OutcomeKey:
    """按优先级识别并点击妃妃三选一选项。"""
    for path, label in _OPTION_PRIORITY:
        hit = m.find(path, timeout=0.8, threshold=0.8)
        if hit.found and hit.center:
            cx, cy = hit.center
            logger.info("妃妃选项 → %s @ (%s,%s) conf=%.3f", label, cx, cy, hit.confidence)
            m.reason = f"选中={label}"
            key = do(move().to(cx, cy).raw(), click())(m)
            return key if key is not None else FULFILLED

    m.reason = "未识别到 我来帮你/快睡午觉/讨价还价"
    logger.info("choose_option → rejected")
    return REJECTED
