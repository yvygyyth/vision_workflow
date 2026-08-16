"""千里单骑 · 锦囊事件动作。"""

from __future__ import annotations

import logging
import random
import time

from vision_workflow.apps.ming_jiang_sha.common.paths import DATA_ROOT
from vision_workflow.apps.ming_jiang_sha.parts.qian_li_dan_qi.fight.actions import (
    cancel_visible,
)
from vision_workflow.input import Mouse
from vision_workflow.module import ModuleContext
from vision_workflow.status import FULFILLED, OutcomeKey
from vision_workflow.vision import find_all_images

logger = logging.getLogger(__name__)

_DIR = f"{DATA_ROOT}/qian_li_dan_qi/pocket_event"
# 资源文件名拼写保持与磁盘一致
_EVENT_PATTERN = f"{_DIR}/event_patterm.png"

# 点完后稍等 UI 刷新
_AFTER_CLICK_SEC = 0.6

# Flow 出口：出现取消 → 进 in_battle
ENTER_BATTLE = "in_battle"


def pick_event_pattern(m: ModuleContext) -> OutcomeKey:
    """找到的花纹里随机点一个；一个都没有则本 Flow 结束。"""
    hits = find_all_images(m.resolve(_EVENT_PATTERN), threshold=0.8, max_count=16)
    if not hits:
        m.reason = "未找到 event_pattern，锦囊事件结束"
        logger.info("pick_event_pattern → fulfilled（无匹配）")
        return FULFILLED

    hit = random.choice(hits)
    if not hit.center:
        m.reason = "匹配无中心点"
        logger.warning("pick_event_pattern 匹配无 center，当作结束")
        return FULFILLED

    cx, cy = hit.center
    logger.info(
        "pick_event_pattern 候选=%s 随机点击 @ (%s,%s) conf=%.3f",
        len(hits),
        cx,
        cy,
        hit.confidence,
    )
    Mouse().move(cx, cy).click().sleep(0.2).perform()
    time.sleep(_AFTER_CLICK_SEC)
    m.reason = f"点击花纹 1/{len(hits)}"
    return "clicked"


def check_cancel_ready(m: ModuleContext) -> OutcomeKey:
    """点花纹后：有取消 → in_battle；没有 → 继续点花纹。"""
    if cancel_visible(m):
        m.reason = "取消已出现，进入战斗"
        logger.info("check_cancel_ready → in_battle")
        return ENTER_BATTLE

    m.reason = "取消未出现，继续点花纹"
    logger.info("check_cancel_ready → continue")
    return "continue"
