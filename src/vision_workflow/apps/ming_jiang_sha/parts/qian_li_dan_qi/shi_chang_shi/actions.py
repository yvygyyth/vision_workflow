"""千里单骑 · 十常侍事件动作。"""

from __future__ import annotations

import logging
import time

from vision_workflow.apps.ming_jiang_sha.common.paths import DATA_ROOT
from vision_workflow.apps.ming_jiang_sha.parts.qian_li_dan_qi.fight.actions import (
    cancel_visible,
)
from vision_workflow.events import click, do, move
from vision_workflow.module import ModuleContext
from vision_workflow.status import FULFILLED, OutcomeKey, REJECTED

logger = logging.getLogger(__name__)

_DIR = f"{DATA_ROOT}/qian_li_dan_qi/shi_chang_shi"
_ATTACK = f"{_DIR}/attack.png"
_ATTACK_ROUNDS_KEY = "shi_chang_shi_attack_rounds"
_MAX_ATTACK_ROUNDS = 8
_AFTER_ATTACK_SEC = 0.5


def click_attack(m: ModuleContext) -> OutcomeKey:
    """连点 attack 五下；轮次过多则失败。"""
    rounds = int(m.vars.get(_ATTACK_ROUNDS_KEY, 0)) + 1
    m.vars[_ATTACK_ROUNDS_KEY] = rounds
    if rounds > _MAX_ATTACK_ROUNDS:
        m.reason = f"已攻击 {_MAX_ATTACK_ROUNDS} 轮仍未出现取消"
        logger.error("click_attack 超限 rounds=%s", rounds)
        return REJECTED

    logger.info("click_attack 第 %s 轮，连点 5 下", rounds)
    key = do(move().image(_ATTACK), click().times(5))(m)
    time.sleep(_AFTER_ATTACK_SEC)
    return key if key is not None else FULFILLED


def check_cancel_ready(m: ModuleContext) -> OutcomeKey:
    """取消按钮已出现 → fulfilled；否则 need_attack 再点图。"""
    if cancel_visible(m):
        m.vars.pop(_ATTACK_ROUNDS_KEY, None)
        m.reason = "取消已出现，进入开打"
        logger.info("check_cancel_ready → fulfilled")
        return FULFILLED

    m.reason = "取消未出现，继续点 attack"
    logger.info("check_cancel_ready → need_attack")
    return "need_attack"
