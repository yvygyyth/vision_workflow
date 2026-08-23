"""事件三选一（跳过诸葛亮）。"""

from __future__ import annotations

import logging
import time

from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.detect import relocate_pick_event
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.signals import PICK_EVENT_DETECT, snap_center, snap_found
from vision_bot.core.input import Mouse
from vision_bot.runtime.flow import Flow, StepResult
from vision_bot.runtime.types import END, FEI_FEI, MO_ZI, SHI_CHANG_SHI, STILL_HERE

logger = logging.getLogger(__name__)

_PRIORITY = (
    ("choice.fei_fei", FEI_FEI),
    ("choice.shi_chang_shi", SHI_CHANG_SHI),
    ("choice.mo_zi", MO_ZI),
)


def _choose(ctx) -> StepResult:
    snap = ctx.snap(PICK_EVENT_DETECT)
    for key, outcome in _PRIORITY:
        c = snap_center(snap, key)
        if c:
            Mouse().move(*c).click().sleep(0.2).perform()
            ctx.vars["pending_event"] = outcome
            logger.info("pick_event 选中 %s", outcome)
            return StepResult.ok(next_id="verify")
    return StepResult.fail("无事件选项")


def _verify(ctx) -> StepResult:
    outcome = ctx.vars.get("pending_event")
    if not outcome:
        return StepResult.fail("无 pending 事件")
    key = next(k for k, o in _PRIORITY if o == outcome)
    time.sleep(0.6)
    snap = ctx.snap({key})
    if snap_found(snap, key):
        return StepResult.ok(outcome=STILL_HERE, next_id="choose")
    ctx.vars.pop("pending_event", None)
    return StepResult.end(outcome)


def build() -> Flow:
    return Flow(
        id="pick_event",
        name="事件选择",
        entry="choose",
        relocate=relocate_pick_event,
        steps={
            "choose": _choose,
            "verify": _verify,
        },
        on={
            FEI_FEI: END,
            MO_ZI: END,
            SHI_CHANG_SHI: END,
            STILL_HERE: "choose",
        },
    )
