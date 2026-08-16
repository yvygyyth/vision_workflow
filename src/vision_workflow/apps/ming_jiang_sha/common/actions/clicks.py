"""common 图点击：跨流程复用的 UI（与 parts 专属动作区分）。"""

from __future__ import annotations

from vision_workflow.apps.ming_jiang_sha.common.paths import COMMON_DIR
from vision_workflow.events import click, do, move
from vision_workflow.events.support.find import wait_image
from vision_workflow.module import EventFn, ModuleContext
from vision_workflow.status import FULFILLED, REJECTED, OutcomeKey

click_max: EventFn = do(move().image(f"{COMMON_DIR}/max.png"), click())
click_ming_jiang_ce: EventFn = do(move().image(f"{COMMON_DIR}/ming_jiang_ce.png"), click())
click_ling_xi_box: EventFn = do(move().image(f"{COMMON_DIR}/ling_xi-box.png"), click())

_BUY_BELOW_PX = 10
_BUY_IMAGE = f"{COMMON_DIR}/buy.png"


def click_buy(*, pause: float = 0.2, below_px: int = _BUY_BELOW_PX) -> EventFn:
    """购买：识 buy.png 顶边花纹，移到底边中点下方 below_px 再点击。"""

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
        m.mouse().move(cx, cy).click().sleep(pause).perform()
        return FULFILLED

    return _event


buy: EventFn = click_buy()
