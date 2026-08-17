"""千里单骑 · 三选一动作。"""

from __future__ import annotations

import logging
import time
from enum import Enum

from vision_workflow.apps.ming_jiang_sha.common.paths import COMMON_DIR, DATA_ROOT
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
CHOICE_REGION: tuple[int, int, int, int] = (800, 350, 1630, 780)

_CHALLENGE = f"{_DIR}/challenge.png"
_CHALLENGE_HELP = f"{_DIR}/challenge_help.png"
_BA_QING_STORE = f"{_DIR}/ba_qing_store.png"
_POCKET_EVENT = f"{_DIR}/pocket_event.png"
_REST = f"{_DIR}/rest.png"
_ZHU_GE_LIANG = f"{_DIR}/zhu_ge_liangf.png"
_FEI_FEI = f"{_DIR}/fei_fei.png"
_SHI_CHANG_SHI = f"{_DIR}/shi_chang_shi.png"
_CONFIRM = f"{COMMON_DIR}/confirm.png"
_SHOP = (
    _BA_QING_STORE,
    _REST,
    f"{_DIR}/lv_bu_wei_store.png",
    _POCKET_EVENT,
)
_EVENT = (
    _FEI_FEI,
    _SHI_CHANG_SHI,
    _ZHU_GE_LIANG,
)
# 铜币 ≥ 此值才尝试点巴清商店
_BA_QING_COPPER_MIN = 30
# 点选后等 UI 切换再核验图标是否消失
_ENTER_WAIT_SEC = 0.6
PENDING_EVENT_KEY = "pending_event_choice"

# Flow 对外：本轮游戏结束（确认+关弹窗后，工作流停止）
RUN_ENDED = "run_ended"


class ShopChoice(str, Enum):
    """商店分支选中的选项（兼作 Module / Flow 路由 key）。"""

    BA_QING_STORE = "ba_qing_store"
    POCKET_EVENT = "pocket_event"
    REST = "rest"


class EventChoice(str, Enum):
    """事件分支选中的选项（兼作 Module / Flow 路由 key）。"""

    ZHU_GE_LIANG = "zhu_ge_liang"
    FEI_FEI = "fei_fei"
    SHI_CHANG_SHI = "shi_chang_shi"


# 枚举 → 图标（核验进场用）
_EVENT_IMAGE: dict[EventChoice, str] = {
    EventChoice.FEI_FEI: _FEI_FEI,
    EventChoice.SHI_CHANG_SHI: _SHI_CHANG_SHI,
    EventChoice.ZHU_GE_LIANG: _ZHU_GE_LIANG,
}
# 点选优先级：妃妃 → 十常侍 → 诸葛亮
_EVENT_CANDIDATES: tuple[tuple[str, EventChoice], ...] = (
    (_EVENT_IMAGE[EventChoice.FEI_FEI], EventChoice.FEI_FEI),
    (_EVENT_IMAGE[EventChoice.SHI_CHANG_SHI], EventChoice.SHI_CHANG_SHI),
    (_EVENT_IMAGE[EventChoice.ZHU_GE_LIANG], EventChoice.ZHU_GE_LIANG),
)


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
    """判定：战斗 > 商店 > 事件 > 本轮结束确认框；未识别则 REJECTED（模块重试）。"""
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

    # 结算后无三选一、出现公共确认 → 本轮结束
    if m.find(_CONFIRM, timeout=0.0, threshold=0.8).found:
        m.reason = "识别到结算确认，本轮结束"
        logger.info("detect_choice → run_ended")
        return RUN_ENDED

    m.reason = "选择区内未识别到战斗/商店/事件，也无结算确认"
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
    """按铜币优先选：巴清商店(≥30) → 锦囊事件 → 休息；全未识别则 REJECTED。"""
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


def confirm_ba_qing_entered(m: ModuleContext) -> OutcomeKey:
    """点巴清后核验：图标消失 → 已进店；仍在 → 未进店。"""
    time.sleep(_ENTER_WAIT_SEC)
    if _probe_in_choice(m, _BA_QING_STORE):
        m.reason = "巴清图标仍在，未进入商店"
        logger.info("confirm_ba_qing_entered → still_here")
        return "still_here"
    logger.info("confirm_ba_qing_entered → ba_qing_store")
    return ShopChoice.BA_QING_STORE


def choose_event(m: ModuleContext) -> OutcomeKey:
    """在妃妃 / 十常侍 / 诸葛亮中点第一个找到的；写入 pending 供进场核验。"""
    for path, choice in _EVENT_CANDIDATES:
        hit = _find_in_choice(m, path, timeout=0.8)
        if hit.found and _click_center(hit, label=choice.value):
            m.vars[PENDING_EVENT_KEY] = choice
            m.reason = f"选中事件={choice.value}"
            logger.info("choose_event → %s", choice.value)
            return choice

    m.reason = "事件分支未找到 fei_fei/shi_chang_shi/zhu_ge_liang"
    logger.error("choose_event 失败：%s", m.reason)
    return REJECTED


def confirm_event_entered(m: ModuleContext) -> OutcomeKey:
    """点事件后核验：对应图标消失 → 已进入；仍在 → 未进入。"""
    choice = m.vars.get(PENDING_EVENT_KEY)
    if not isinstance(choice, EventChoice):
        m.reason = "无 pending 事件选择"
        logger.error("confirm_event_entered 缺少 pending_event_choice")
        return REJECTED

    time.sleep(_ENTER_WAIT_SEC)
    image = _EVENT_IMAGE[choice]
    if _probe_in_choice(m, image):
        m.reason = f"{choice.value} 图标仍在，未进入事件"
        logger.info("confirm_event_entered → still_here (%s)", choice.value)
        return "still_here"

    m.vars.pop(PENDING_EVENT_KEY, None)
    logger.info("confirm_event_entered → %s", choice.value)
    return choice
