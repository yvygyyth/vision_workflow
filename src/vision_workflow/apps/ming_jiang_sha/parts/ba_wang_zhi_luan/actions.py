"""八王之乱 · 全部动作。"""

from __future__ import annotations

import logging
import time

from vision_workflow.apps.ming_jiang_sha.common.paths import DATA_ROOT
from vision_workflow.events import click, do, move
from vision_workflow.events.support.find import wait_image
from vision_workflow.input import Mouse
from vision_workflow.module import EventFn, ModuleContext
from vision_workflow.status import FULFILLED, OutcomeKey, REJECTED
from vision_workflow.vision import find_all_images

logger = logging.getLogger(__name__)

_DIR = f"{DATA_ROOT}/ba_wang_zhi_luan"
_FIGHT_DIR = f"{DATA_ROOT}/qian_li_dan_qi/fight"

_ZHUN_BEI = f"{_DIR}/zhun_bei.png"
_UN_ZHUN_BEI = f"{_DIR}/un_zhun+bei.png"
_START = f"{_DIR}/start.png"
_SIX = f"{_DIR}/6.png"
_OK = f"{_DIR}/ok.png"

_SETTING = f"{_FIGHT_DIR}/setting.png"
_AUTO = f"{_FIGHT_DIR}/auto.png"
_CHALLENGE_END = f"{_FIGHT_DIR}/challenge_end.png"
_NEXT_STEP = f"{_FIGHT_DIR}/next_step.png"

_MAX_SIX = 13
_AFTER_SIX_CLICK_SEC = 0.35
_WAIT_INTERVAL_SEC = 1.0
_WAIT_TIMEOUT_SEC = 600.0

ENTER_BATTLE = "in_battle"


def _probe(m: ModuleContext, image: str, *, timeout: float = 0.8) -> bool:
    hit = wait_image(
        m,
        (image,),
        threshold=0.8,
        timeout=timeout,
        interval=0.3,
        region=None,
        grayscale=None,
    )
    return hit is not None and hit.found


def _setting_visible(m: ModuleContext, *, timeout: float = 0.8) -> bool:
    return bool(m.find(_SETTING, timeout=timeout, threshold=0.8).found)


# ── 房间准备 ──────────────────────────────────────────────────────────


def detect_role(m: ModuleContext) -> OutcomeKey:
    """房员：准备 / 取消准备；其余视为房主（轮询开始）。"""
    if _probe(m, _UN_ZHUN_BEI):
        logger.info("detect_role → member_ready")
        return "member_ready"
    if _probe(m, _ZHUN_BEI):
        logger.info("detect_role → member")
        return "member"
    logger.info("detect_role → owner")
    return "owner"


def click_ready(m: ModuleContext) -> OutcomeKey:
    """房员：识别「准备」并点击。"""
    hit = wait_image(
        m,
        (_ZHUN_BEI,),
        threshold=0.8,
        timeout=1.5,
        interval=0.3,
        region=None,
        grayscale=None,
    )
    if hit is None or not hit.center:
        m.reason = "未找到准备按钮"
        return REJECTED

    cx, cy = hit.center
    logger.info("click_ready @ (%s,%s)", cx, cy)
    Mouse().move(cx, cy).click().sleep(0.2).perform()
    m.reason = "已点击准备"
    return FULFILLED


def confirm_ready(m: ModuleContext) -> OutcomeKey:
    """点击后核验是否变为「取消准备」。"""
    time.sleep(0.5)
    if _probe(m, _UN_ZHUN_BEI, timeout=1.0):
        m.reason = "已变为取消准备"
        logger.info("confirm_ready → fulfilled")
        return FULFILLED
    if _probe(m, _ZHUN_BEI, timeout=0.5):
        m.reason = "仍为准备，重试点击"
        logger.info("confirm_ready → still_ready")
        return "still_ready"

    m.reason = "点击准备后未识别到取消准备"
    return REJECTED


poll_click_start: EventFn = do(
    move().image(_START).match(timeout=600, interval=1.5),
    click().pause(0.3),
)


# ── 选将 ──────────────────────────────────────────────────────────────


def wait_game_start(m: ModuleContext) -> OutcomeKey:
    """等待选将或战斗 UI（6 / setting）出现。"""
    deadline = time.monotonic() + _WAIT_TIMEOUT_SEC
    while time.monotonic() < deadline:
        if find_all_images(m.resolve(_SIX), threshold=0.8, max_count=1):
            m.reason = "选将阶段已开始"
            logger.info("wait_game_start → pick_six")
            return FULFILLED
        if _setting_visible(m, timeout=0.3):
            m.reason = "已进入战斗，跳过选将"
            logger.info("wait_game_start → in_battle")
            return ENTER_BATTLE
        time.sleep(_WAIT_INTERVAL_SEC)

    m.reason = "等待开局超时"
    return REJECTED


def pick_all_sixes(m: ModuleContext) -> OutcomeKey:
    """扫描一次，依次点击场上所有「6」。"""
    hits = find_all_images(m.resolve(_SIX), threshold=0.8, max_count=_MAX_SIX)
    sorted_hits = sorted(
        (hit for hit in hits if hit.center),
        key=lambda hit: (hit.center[1], hit.center[0]),
    )

    for hit in sorted_hits:
        cx, cy = hit.center
        assert cx is not None and cy is not None
        logger.info(
            "pick_all_sixes @ (%s,%s) conf=%.3f",
            cx,
            cy,
            hit.confidence,
        )
        Mouse().move(cx, cy).click().sleep(0.2).perform()
        time.sleep(_AFTER_SIX_CLICK_SEC)

    if sorted_hits:
        m.reason = f"点6×{len(sorted_hits)}，等待进入战斗"
    else:
        m.reason = "场上无6，等待 setting 出现"
    logger.info("pick_all_sixes → %s", m.reason)
    return FULFILLED


def click_ok_if_any(m: ModuleContext) -> OutcomeKey:
    """识别确定按钮，有则点；没有也继续等 setting。"""
    hit = m.find(_OK, timeout=1.0, threshold=0.8)
    if hit.found and hit.center:
        cx, cy = hit.center
        logger.info("click_ok_if_any @ (%s,%s) conf=%.3f", cx, cy, hit.confidence)
        Mouse().move(cx, cy).click().sleep(0.2).perform()
        m.reason = "已点确定"
    else:
        m.reason = "无确定按钮"
    logger.info("click_ok_if_any → %s", m.reason)
    return FULFILLED


# ── 无赠礼战斗 ────────────────────────────────────────────────────────

move_aside: EventFn = do(move().to(80, 80).raw())

wait_click_setting: EventFn = do(
    move().image(_SETTING).match(timeout=600, interval=0.5),
    click().pause(0.3),
)

click_auto: EventFn = do(move().image(_AUTO), click())
click_challenge_end: EventFn = do(
    move().image(_CHALLENGE_END).match(timeout=1200, interval=5),
    click(),
)


def click_next_step_if_any(m: ModuleContext) -> OutcomeKey:
    """有「下一步」就点；没有也算过。"""
    clicked = 0
    for _ in range(5):
        hit = m.find(_NEXT_STEP, timeout=1.2, threshold=0.8)
        if not hit.found or not hit.center:
            break
        cx, cy = hit.center
        logger.info("click_next_step_if_any @ (%s,%s)", cx, cy)
        do(move().to(cx, cy).raw(), click())(m)
        clicked += 1
        time.sleep(0.4)
    m.reason = f"点下一步×{clicked}" if clicked else "无下一步"
    logger.info("click_next_step_if_any → %s", m.reason)
    return FULFILLED


def battle_round_done(m: ModuleContext) -> OutcomeKey:
    """本局结束，回到房间准备环节。"""
    m.reason = "战斗结束，回房间准备"
    logger.info("battle_round_done → detect_role")
    return FULFILLED
