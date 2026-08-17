"""千里单骑 · 锦囊事件动作。"""

from __future__ import annotations

import logging
import random
import time

from vision_workflow.apps.ming_jiang_sha.common.paths import DATA_ROOT
from vision_workflow.apps.ming_jiang_sha.parts.qian_li_dan_qi.fight.actions import (
    cancel_visible,
)
from vision_workflow.events import click, do, move
from vision_workflow.input import Mouse
from vision_workflow.module import ModuleContext
from vision_workflow.status import FULFILLED, REJECTED, OutcomeKey
from vision_workflow.vision import find_all_images

logger = logging.getLogger(__name__)

_DIR = f"{DATA_ROOT}/qian_li_dan_qi/pocket_event"
# 资源文件名拼写保持与磁盘一致
_EVENT_PATTERN = f"{_DIR}/event_patterm.png"
_OK = f"{_DIR}/ok.png"

# 点完后稍等 UI 刷新
_AFTER_CLICK_SEC = 0.6
# 未匹配时多扫几轮，避免偶发漏识别就退出
_FIND_ROUNDS = 5
_FIND_INTERVAL_SEC = 0.4

# Flow 出口：出现取消 → 进 in_battle
ENTER_BATTLE = "in_battle"
# 花纹已空：检查取消/确认后若都没有则结束（不再点花纹）
_DONE_KEY = "pocket_event_done"
# 已点确认：只等取消，不再点花纹、不再点确认
_OK_CLICKED_KEY = "pocket_ok_clicked"


def _ok_visible(m: ModuleContext, *, timeout: float = 0.5) -> bool:
    return bool(m.find(_OK, timeout=timeout, threshold=0.8).found)


def pick_event_pattern(m: ModuleContext) -> OutcomeKey:
    """找到的花纹里随机点一个；多轮仍没有则去看取消/确认。"""
    hits = None
    for round_i in range(1, _FIND_ROUNDS + 1):
        hits = find_all_images(m.resolve(_EVENT_PATTERN), threshold=0.8, max_count=16)
        if hits:
            if round_i > 1:
                logger.info(
                    "pick_event_pattern 第 %s/%s 轮识别到 %s 个",
                    round_i,
                    _FIND_ROUNDS,
                    len(hits),
                )
            break
        logger.info("pick_event_pattern 第 %s/%s 轮未匹配", round_i, _FIND_ROUNDS)
        if round_i < _FIND_ROUNDS:
            time.sleep(_FIND_INTERVAL_SEC)

    if not hits:
        m.vars[_DONE_KEY] = True
        m.reason = "多轮未找到 event_pattern，去看取消/确认"
        logger.info("pick_event_pattern → check（%s 轮无匹配）", _FIND_ROUNDS)
        return "check"

    hit = random.choice(hits)
    if not hit.center:
        m.vars[_DONE_KEY] = True
        m.reason = "匹配无中心点，去看取消/确认"
        logger.warning("pick_event_pattern 匹配无 center → check")
        return "check"

    m.vars.pop(_DONE_KEY, None)
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


def check_after_pattern(m: ModuleContext) -> OutcomeKey:
    """看取消/确认：取消→战斗；确认→点 ok；点过确认后只等取消。"""
    if cancel_visible(m):
        m.vars.pop(_DONE_KEY, None)
        m.vars.pop(_OK_CLICKED_KEY, None)
        m.reason = "取消已出现，进入无赠礼战斗"
        logger.info("check_after_pattern → in_battle")
        return ENTER_BATTLE

    # 已点确认：只等取消出现
    if m.vars.get(_OK_CLICKED_KEY):
        m.reason = "已点确认，等待取消"
        logger.info("check_after_pattern → rejected（等取消）")
        return REJECTED

    if _ok_visible(m):
        m.vars.pop(_DONE_KEY, None)
        m.reason = "确认已出现，先点确认"
        logger.info("check_after_pattern → need_ok")
        return "need_ok"

    if m.vars.pop(_DONE_KEY, False):
        m.reason = "无花纹且无取消/确认，结束"
        logger.info("check_after_pattern → fulfilled（结束）")
        return FULFILLED

    m.reason = "取消/确认未出现，继续点花纹"
    logger.info("check_after_pattern → continue")
    return "continue"


def click_ok(m: ModuleContext) -> OutcomeKey:
    """点击 ok 确认，然后回到 check_after 等取消。"""
    hit = m.find(_OK, timeout=0.8, threshold=0.8)
    if not (hit.found and hit.center):
        m.reason = "确认按钮未找到"
        logger.warning("click_ok → rejected")
        return REJECTED

    cx, cy = hit.center
    logger.info("click_ok @ (%s,%s) conf=%.3f", cx, cy, hit.confidence)
    do(move().to(cx, cy).raw(), click())(m)
    time.sleep(0.3)
    m.vars[_OK_CLICKED_KEY] = True
    m.reason = "点到确认，去看取消"
    return FULFILLED
