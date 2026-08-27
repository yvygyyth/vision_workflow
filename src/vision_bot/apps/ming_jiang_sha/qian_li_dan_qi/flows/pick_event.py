"""事件三选一 mod。"""

from __future__ import annotations

import logging
import time

from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.ids import qmod
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.signals import PICK_EVENT_DETECT, snap_center, snap_found
from vision_bot.core.input import Mouse
from vision_bot.perception.snapshot import ScreenSnapshot, capture
from vision_bot.runtime.context import RunContext
from vision_bot.runtime.result import Result

logger = logging.getLogger(__name__)

_PRIORITY = (
    ("choice.fei_fei", "fei_fei"),
    ("choice.shi_chang_shi", "shi_chang_shi"),
    ("choice.mo_zi", "mo_zi"),
)


def detect(snap: ScreenSnapshot, ctx: RunContext | None = None) -> str | None:
    if any(snap_found(snap, k) for k in ("choice.fei_fei", "choice.shi_chang_shi", "choice.mo_zi")):
        return qmod("battle_hub.pick_event", "choose")
    return None


def relocate(ctx: RunContext) -> str | None:
    snap = capture(ctx.registry, ctx.base_dir, PICK_EVENT_DETECT)
    return detect(snap, ctx)


def choose(ctx) -> Result:
    snap = ctx.snap(PICK_EVENT_DETECT)
    for key, outcome in _PRIORITY:
        c = snap_center(snap, key)
        if c:
            Mouse().move(*c).click().sleep(0.2).perform()
            ctx.vars["pending_event"] = outcome
            logger.info("pick_event 选中 %s", outcome)
            ctx.goto(qmod("battle_hub.pick_event", "verify"))
            return Result.success()
    return Result.fail("无事件选项")


def verify(ctx) -> Result:
    outcome = ctx.vars.get("pending_event")
    if not outcome:
        return Result.fail("无 pending 事件")
    key = next(k for k, o in _PRIORITY if o == outcome)
    time.sleep(0.6)
    snap = ctx.snap({key})
    if snap_found(snap, key):
        ctx.goto(qmod("battle_hub.pick_event", "choose"))
        return Result.success()
    ctx.vars.pop("pending_event", None)
    ctx.goto(f"qldq.{outcome}")
    return Result.success()
