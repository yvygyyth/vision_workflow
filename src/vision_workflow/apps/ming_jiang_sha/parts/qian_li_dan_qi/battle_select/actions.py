"""千里单骑 · 三选一动作。"""

from __future__ import annotations

import logging
import time
from enum import Enum

from vision_workflow.apps.ming_jiang_sha.common.paths import DATA_ROOT
from vision_workflow.apps.ming_jiang_sha.parts.qian_li_dan_qi.utils import (
    get_battle_state,
    refresh_copper_coins,
)
from vision_workflow.events import click, do, move
from vision_workflow.input import Mouse
from vision_workflow.module import ModuleContext
from vision_workflow.status import FULFILLED, REJECTED, OutcomeKey

logger = logging.getLogger(__name__)

_DIR = f"{DATA_ROOT}/qian_li_dan_qi/battle_select"

# 三选一图标区（相对模板基准分辨率；识图时自动 fit）
CHOICE_REGION: tuple[int, int, int, int] = (800, 350, 1630, 780)

# 多处复用的模板
_CHALLENGE = f"{_DIR}/challenge.png"
_BA_QING_STORE = f"{_DIR}/ba_qing_store.png"
_POCKET_EVENT = f"{_DIR}/pocket_event.png"
_REST = f"{_DIR}/rest.png"

PENDING_EVENT_KEY = "pending_event_choice"


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
    MO_ZI = "mo_zi"


# 枚举 → 图标（点选 + 进场核验；顺序即优先级，墨子最低）
_EVENT_IMAGE: dict[EventChoice, str] = {
    EventChoice.FEI_FEI: f"{_DIR}/fei_fei.png",
    EventChoice.SHI_CHANG_SHI: f"{_DIR}/shi_chang_shi.png",
    EventChoice.ZHU_GE_LIANG: f"{_DIR}/zhu_ge_liangf.png",
    EventChoice.MO_ZI: f"{_DIR}/mo_zi.png",
}


def _find_in_choice(m: ModuleContext, image: str, *, timeout: float = 0.0):
    return m.find(image, region=CHOICE_REGION, timeout=timeout, threshold=0.8)


def _probe_in_choice(m: ModuleContext, image: str) -> bool:
    return bool(_find_in_choice(m, image).found)


def _click_center(hit, *, label: str, times: int = 1) -> bool:
    if not hit.center:
        return False
    cx, cy = hit.center
    n = max(times, 1)
    logger.info("点击 %s @ (%s,%s) ×%s", label, cx, cy, n)
    Mouse().move(cx, cy).click(clicks=n).sleep(0.2).perform()
    return True


def dismiss_up_panel(m: ModuleContext) -> OutcomeKey:
    """若出现「武将技能」(up.png)，绝对坐标点击收起，再继续三选一判定。"""
    hit = m.find(f"{_DIR}/up.png", timeout=0.5, threshold=0.8)
    if not hit.found:
        m.reason = "无武将技能面板"
        logger.info("dismiss_up_panel → skip")
        return FULFILLED

    logger.info("dismiss_up_panel 识别到 up，绝对点击 (1300,1150)")
    do(move().to(1300, 1150).raw(), click())(m)
    time.sleep(0.4)
    m.reason = "点掉武将技能 @ (1300,1150)"
    return FULFILLED


def detect_choice(m: ModuleContext) -> OutcomeKey:
    """判定：战斗 > 商店 > 事件；都没有则 REJECTED（模块重试，耗尽后再交给进战）。
    """
    if _probe_in_choice(m, _CHALLENGE):
        logger.info("detect_choice → battle")
        return "battle"

    for path in (
        _BA_QING_STORE,
        _REST,
        f"{_DIR}/lv_bu_wei_store.png",
        _POCKET_EVENT,
    ):
        if _probe_in_choice(m, path):
            logger.info("detect_choice → shop (%s)", path.rsplit("/", 1)[-1])
            return "shop"

    for path in _EVENT_IMAGE.values():
        if _probe_in_choice(m, path):
            logger.info("detect_choice → event (%s)", path.rsplit("/", 1)[-1])
            return "event"

    m.reason = "选择区内未识别到战斗/商店/事件"
    logger.info("detect_choice → rejected")
    return REJECTED


def choose_battle(m: ModuleContext) -> OutcomeKey:
    """优先点「驰援/助战」类 challenge_help；否则点选择区内第一个 challenge。"""
    help_hit = _find_in_choice(m, f"{_DIR}/challenge_help.png", timeout=0.8)
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
    if coins >= 30:
        candidates.append((_BA_QING_STORE, ShopChoice.BA_QING_STORE))
    candidates.extend(
        (
            (_POCKET_EVENT, ShopChoice.POCKET_EVENT),
            (_REST, ShopChoice.REST),
        )
    )

    for path, choice in candidates:
        hit = _find_in_choice(m, path, timeout=0.8)
        if hit.found and _click_center(hit, label=choice.value, times=2):
            m.reason = f"铜币={coins} 选中={choice.value}（点两次）"
            logger.info("choose_shop → %s (铜币=%s, 点两次)", choice.value, coins)
            return choice

    m.reason = f"铜币={coins} 未识别到 ba_qing_store/pocket_event/rest"
    logger.error("choose_shop 失败：%s", m.reason)
    return REJECTED


def confirm_ba_qing_entered(m: ModuleContext) -> OutcomeKey:
    """点巴清后核验：图标消失 → 已进店；仍在 → 未进店。"""
    time.sleep(0.6)
    if _probe_in_choice(m, _BA_QING_STORE):
        m.reason = "巴清图标仍在，未进入商店"
        logger.info("confirm_ba_qing_entered → still_here")
        return "still_here"
    logger.info("confirm_ba_qing_entered → ba_qing_store")
    return ShopChoice.BA_QING_STORE


def choose_event(m: ModuleContext) -> OutcomeKey:
    """按表顺序点第一个找到的事件（墨子最低）；写入 pending 供进场核验。"""
    for choice, path in _EVENT_IMAGE.items():
        hit = _find_in_choice(m, path, timeout=0.8)
        if hit.found and _click_center(hit, label=choice.value):
            m.vars[PENDING_EVENT_KEY] = choice
            m.reason = f"选中事件={choice.value}"
            logger.info("choose_event → %s", choice.value)
            return choice

    m.reason = "事件分支未找到 fei_fei/shi_chang_shi/zhu_ge_liang/mo_zi"
    logger.error("choose_event 失败：%s", m.reason)
    return REJECTED


def confirm_event_entered(m: ModuleContext) -> OutcomeKey:
    """点事件后核验：对应图标消失 → 已进入；仍在 → 未进入。"""
    choice = m.vars.get(PENDING_EVENT_KEY)
    if not isinstance(choice, EventChoice):
        m.reason = "无 pending 事件选择"
        logger.error("confirm_event_entered 缺少 pending_event_choice")
        return REJECTED

    time.sleep(0.6)
    if _probe_in_choice(m, _EVENT_IMAGE[choice]):
        m.reason = f"{choice.value} 图标仍在，未进入事件"
        logger.info("confirm_event_entered → still_here (%s)", choice.value)
        return "still_here"

    m.vars.pop(PENDING_EVENT_KEY, None)
    logger.info("confirm_event_entered → %s", choice.value)
    return choice
