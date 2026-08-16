"""千里单骑 · 三选一动作。"""

from __future__ import annotations

from vision_workflow.apps.ming_jiang_sha.common.paths import DATA_ROOT
from vision_workflow.module import EventFn, ModuleContext
from vision_workflow.status import FULFILLED, REJECTED, OutcomeKey

_DIR = f"{DATA_ROOT}/qian_li_dan_qi/battle"

# 三选一图标区（相对模板基准分辨率；识图时自动 fit）
CHOICE_REGION: tuple[int, int, int, int] = (1130, 350, 1300, 780)

_CHALLENGE = f"{_DIR}/challenge.png"
_CHALLENGE_HELP = f"{_DIR}/challenge_help.png"
_SHOP = (
    f"{_DIR}/ba_qing_store.png",
    f"{_DIR}/rest.png",
    f"{_DIR}/lv_bu_wei_store.png",
)
_EVENT = (
    f"{_DIR}/zhu_ge_liangf.png",
    f"{_DIR}/fei_fei.png",
    f"{_DIR}/zuo_ci.png",
)


def _find_in_choice(m: ModuleContext, image: str, *, timeout: float = 0.0):
    return m.find(image, region=CHOICE_REGION, timeout=timeout, threshold=0.8)


def _probe_in_choice(m: ModuleContext, image: str) -> bool:
    return bool(_find_in_choice(m, image).found)


def _click_center(m: ModuleContext, hit, *, label: str) -> bool:
    if not hit.center:
        return False
    cx, cy = hit.center
    m.log("点击 %s @ (%s,%s)", label, cx, cy)
    m.mouse().move(cx, cy).click().sleep(0.2).perform()
    return True


def detect_choice(m: ModuleContext) -> OutcomeKey:
    """判定本轮三选一类型：战斗 > 商店 > 事件；未识别则 REJECTED（交给模块重试）。"""
    if _probe_in_choice(m, _CHALLENGE):
        m.log("detect_choice → battle")
        return "battle"

    for path in _SHOP:
        if _probe_in_choice(m, path):
            m.log("detect_choice → shop (%s)", path.rsplit("/", 1)[-1])
            return "shop"

    for path in _EVENT:
        if _probe_in_choice(m, path):
            m.log("detect_choice → event (%s)", path.rsplit("/", 1)[-1])
            return "event"

    m.reason = "选择区内未识别到战斗/商店/事件"
    m.log("detect_choice → rejected")
    return REJECTED


def choose_battle(m: ModuleContext) -> OutcomeKey:
    """优先点「驰援/助战」类 challenge_help；否则点选择区内第一个 challenge。"""
    help_hit = _find_in_choice(m, _CHALLENGE_HELP, timeout=0.8)
    if help_hit.found and _click_center(m, help_hit, label="challenge_help"):
        return FULFILLED

    challenge_hit = _find_in_choice(m, _CHALLENGE, timeout=0.8)
    if challenge_hit.found and _click_center(m, challenge_hit, label="challenge"):
        return FULFILLED

    m.reason = "战斗分支未找到 challenge_help / challenge"
    return REJECTED


def _stub(name: str) -> EventFn:
    def event(m: ModuleContext) -> OutcomeKey:
        m.log("%s placeholder", name)
        return FULFILLED

    return event


choose_shop: EventFn = _stub("choose_shop")
choose_event: EventFn = _stub("choose_event")
