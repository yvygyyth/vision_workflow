"""千里单骑 · 三选一动作。"""

from __future__ import annotations

import logging
from enum import Enum

from vision_workflow.apps.ming_jiang_sha.common.paths import DATA_ROOT
from vision_workflow.apps.ming_jiang_sha.parts.qian_li_dan_qi.utils import (
    get_battle_state,
    refresh_copper_coins,
)
from vision_workflow.input import Mouse
from vision_workflow.module import ModuleContext
from vision_workflow.status import FULFILLED, REJECTED, OutcomeKey

logger = logging.getLogger(__name__)

_DIR = f"{DATA_ROOT}/qian_li_dan_qi/battle_select"

# 三选一图标区（相对模板基准分辨率；识图时自动 fit）
CHOICE_REGION: tuple[int, int, int, int] = (1130, 350, 1300, 780)

_CHALLENGE = f"{_DIR}/challenge.png"
_CHALLENGE_HELP = f"{_DIR}/challenge_help.png"
_BA_QING_STORE = f"{_DIR}/ba_qing_store.png"
_POCKET_EVENT = f"{_DIR}/pocket_event.png"
_REST = f"{_DIR}/rest.png"
_SHOP = (
    _BA_QING_STORE,
    _REST,
    f"{_DIR}/lv_bu_wei_store.png",
    _POCKET_EVENT,
)
_EVENT = (
    f"{_DIR}/zhu_ge_liangf.png",
    f"{_DIR}/fei_fei.png",
    f"{_DIR}/zuo_ci.png",
)
# 铜币 ≥ 此值才尝试点霸青商店
_BA_QING_COPPER_MIN = 30


class ShopChoice(str, Enum):
    """商店分支选中的选项（兼作 Module / Flow 路由 key）。"""

    BA_QING_STORE = "ba_qing_store"
    POCKET_EVENT = "pocket_event"
    REST = "rest"


def _find_in_choice(m: ModuleContext, image: str, *, timeout: float = 0.0):
    return m.find(image, region=CHOICE_REGION, timeout=timeout, threshold=0.8)


def _probe_in_choice(m: ModuleContext, image: str) -> bool:
    return bool(_find_in_choice(m, image).found)


def _click_center(hit, *, label: str) -> bool:
    if not hit.center:
        return False
    cx, cy = hit.center
    logger.info("点击 %s @ (%s,%s)", label, cx, cy)
    Mouse().move(cx, cy).click().sleep(0.2).perform()
    return True


def detect_choice(m: ModuleContext) -> OutcomeKey:
    """判定本轮三选一类型：战斗 > 商店 > 事件；未识别则 REJECTED（交给模块重试）。"""
    if _probe_in_choice(m, _CHALLENGE):
        logger.info("detect_choice → battle")
        return "battle"

    for path in _SHOP:
        if _probe_in_choice(m, path):
            logger.info("detect_choice → shop (%s)", path.rsplit("/", 1)[-1])
            return "shop"

    for path in _EVENT:
        if _probe_in_choice(m, path):
            logger.info("detect_choice → event (%s)", path.rsplit("/", 1)[-1])
            return "event"

    m.reason = "选择区内未识别到战斗/商店/事件"
    logger.info("detect_choice → rejected")
    return REJECTED


def choose_battle(m: ModuleContext) -> OutcomeKey:
    """优先点「驰援/助战」类 challenge_help；否则点选择区内第一个 challenge。"""
    help_hit = _find_in_choice(m, _CHALLENGE_HELP, timeout=0.8)
    if help_hit.found and _click_center(help_hit, label="challenge_help"):
        return FULFILLED

    challenge_hit = _find_in_choice(m, _CHALLENGE, timeout=0.8)
    if challenge_hit.found and _click_center(challenge_hit, label="challenge"):
        return FULFILLED

    m.reason = "战斗分支未找到 challenge_help / challenge"
    return REJECTED


def update_copper_coins(m: ModuleContext) -> int:
    """OCR 铜币区域，写入 BattleState.copper_coins；失败记 0。"""
    state = get_battle_state(m.ctx)
    amount = refresh_copper_coins(state)
    if amount is None:
        state.copper_coins = 0
        amount = 0
        logger.warning("update_copper_coins 识别失败，铜币记 0")
    else:
        logger.info("update_copper_coins → %s", amount)
    return amount


def choose_shop(m: ModuleContext) -> OutcomeKey:
    """按铜币优先选：霸青商店(≥30) → 锦囊事件 → 休息；全未识别则 REJECTED。"""
    coins = update_copper_coins(m)
    candidates: list[tuple[str, ShopChoice]] = []
    if coins >= _BA_QING_COPPER_MIN:
        candidates.append((_BA_QING_STORE, ShopChoice.BA_QING_STORE))
    candidates.extend(
        (
            (_POCKET_EVENT, ShopChoice.POCKET_EVENT),
            (_REST, ShopChoice.REST),
        )
    )

    for path, choice in candidates:
        hit = _find_in_choice(m, path, timeout=0.8)
        if hit.found and _click_center(hit, label=choice.value):
            m.reason = f"铜币={coins} 选中={choice.value}"
            logger.info("choose_shop → %s (铜币=%s)", choice.value, coins)
            return choice

    m.reason = f"铜币={coins} 未识别到 ba_qing_store/pocket_event/rest"
    logger.error("choose_shop 失败：%s", m.reason)
    return REJECTED


def choose_event(_m: ModuleContext) -> OutcomeKey:
    logger.info("choose_event placeholder")
    return FULFILLED
