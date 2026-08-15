"""common 图点击：跨流程复用的 UI（与 parts 专属 click 区分）。"""

from __future__ import annotations

from vision_workflow.events.builders.click import click
from vision_workflow.events.common.paths import COMMON_DIR
from vision_workflow.events.support.find import wait_image
from vision_workflow.module import EventFn, ModuleContext
from vision_workflow.status import FULFILLED, REJECTED, OutcomeKey

click_max: EventFn = click().image(f"{COMMON_DIR}/max.png").execute()
click_ming_jiang_ce: EventFn = click().image(f"{COMMON_DIR}/ming_jiang_ce.png").execute()
click_ling_xi_box: EventFn = click().image(f"{COMMON_DIR}/ling_xi-box.png").execute()

_BUY_BELOW_PX = 10
_BUY_IMAGE = f"{COMMON_DIR}/buy.png"


def click_buy(*, pause: float = 0.2, below_px: int = _BUY_BELOW_PX) -> EventFn:
    """购买按钮：识 common/buy.png（顶边花纹），点击其底边正中再往下 below_px。"""

    def _event(m: ModuleContext) -> OutcomeKey:
        hit = wait_image(
            m,
            (_BUY_IMAGE,),
            threshold=0.8,
            timeout=3.0,
            interval=0.5,
            region=None,
            grayscale=None,
        )
        if hit is None or not hit.box:
            if not m.reason:
                m.reason = "识图未命中" if hit is None else "识图命中但无 box"
            return REJECTED
        x, y, w, h = hit.box
        cx = x + w // 2
        cy = y + h + below_px
        m.log("click_buy @ (%s,%s) box=%s below=%s", cx, cy, hit.box, below_px)
        m.mouse().at((cx, cy)).click().sleep(pause).perform()
        return FULFILLED

    return _event


# 默认实例，可直接当 Module.event 用
buy: EventFn = click_buy()
