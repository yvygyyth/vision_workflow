"""common 图点击：跨流程复用的 UI（与 parts 专属动作区分）。"""

from __future__ import annotations

import logging

from vision_workflow.apps.ming_jiang_sha.common.paths import COMMON_DIR
from vision_workflow.events import click, do, move
from vision_workflow.events.support.find import wait_image
from vision_workflow.input import Mouse
from vision_workflow.module import EventFn, ModuleContext
from vision_workflow.status import FULFILLED, REJECTED, OutcomeKey

logger = logging.getLogger(__name__)

click_max: EventFn = do(move().image(f"{COMMON_DIR}/max.png"), click())
click_ming_jiang_ce: EventFn = do(move().image(f"{COMMON_DIR}/ming_jiang_ce.png"), click())
click_ling_xi_box: EventFn = do(move().image(f"{COMMON_DIR}/ling_xi-box.png"), click())

_CONFIRM_BELOW_PX = 10
_CONFIRM_IMAGE = f"{COMMON_DIR}/confirm.png"


def click_confirm(*, pause: float = 0.2, below_px: int = _CONFIRM_BELOW_PX) -> EventFn:
    """通用确认框：识 confirm.png 顶边花纹，移到底边中点下方 below_px 再点击。"""

    def _event(m: ModuleContext) -> OutcomeKey:
        hit = wait_image(
            m,
            (_CONFIRM_IMAGE,),
            threshold=0.6,
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
        logger.info("click_confirm @ (%s,%s) box=%s below=%s", cx, cy, hit.box, below_px)
        Mouse().move(cx, cy).click().sleep(pause).perform()
        return FULFILLED

    return _event


confirm: EventFn = click_confirm()
