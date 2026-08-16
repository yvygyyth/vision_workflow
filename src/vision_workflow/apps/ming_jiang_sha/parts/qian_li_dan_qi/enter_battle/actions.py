"""千里单骑 · 进入战斗：确保进入战斗界面。"""

from __future__ import annotations

import logging
import time

from vision_workflow.apps.ming_jiang_sha.common.paths import DATA_ROOT
from vision_workflow.events import click, do, input_text, move
from vision_workflow.events.support.find import wait_image
from vision_workflow.input import Mouse
from vision_workflow.module import EventFn, ModuleContext
from vision_workflow.status import FULFILLED, REJECTED, OutcomeKey

logger = logging.getLogger(__name__)

_DIR = f"{DATA_ROOT}/qian_li_dan_qi/enter_battle"
_SEARCH = f"{_DIR}/search.png"
_START = f"{_DIR}/start.png"
_BATTLE = f"{_DIR}/battle_interface.png"
# 相对「搜索」中心向左到输入框（会走 move 显示缩放）


click_select_wu_jiang: EventFn = do(
    move().image(f"{_DIR}/select_wu_jiang.png"), click()
)

focus_search_input: EventFn = do(
    move().image(_SEARCH),
    move().by(-160, 0),
    click().pause(0.3),
)


def type_wu_jiang(m: ModuleContext) -> OutcomeKey:
    """写入武将名（入参 wu_jiang）。"""
    name = str(m.params.get("wu_jiang", "吕布")).strip()
    if not name:
        m.reason = "入参 wu_jiang 为空"
        return REJECTED
    logger.info("type_wu_jiang %s", name)
    time.sleep(0.2)
    return input_text(name).paste().pause(0.2).execute()(m)


click_search: EventFn = do(move().image(_SEARCH), click())
click_lv_bu: EventFn = do(move().image(f"{_DIR}/lv_bu.png"), click())


def _probe(m: ModuleContext, image: str, *, timeout: float = 1.0):
    return wait_image(
        m,
        (image,),
        threshold=0.8,
        timeout=timeout,
        interval=0.3,
        region=None,
        grayscale=None,
    )


def check_battle_interface(m: ModuleContext) -> OutcomeKey:
    """已在战斗界面 → in_battle；否则 need_prepare。"""
    hit = _probe(m, _BATTLE, timeout=1.0)
    if hit is not None and hit.found:
        logger.info("check_battle_interface → in_battle")
        return "in_battle"
    logger.info("check_battle_interface → need_prepare")
    return "need_prepare"


def try_click_start(m: ModuleContext) -> OutcomeKey:
    """有「开始」则点击；没有则 need_select。"""
    hit = _probe(m, _START, timeout=1.5)
    if hit is None or not hit.center:
        m.reason = "未出现开始按钮，进入武将选择"
        logger.info("try_click_start → need_select")
        return "need_select"

    cx, cy = hit.center
    logger.info("try_click_start 点击开始 @ (%s,%s)", cx, cy)
    try:
        Mouse().move(cx, cy).click().sleep(0.2).perform()
    except Exception as exc:
        m.reason = f"点击开始失败: {exc}"
        return REJECTED
    return FULFILLED
