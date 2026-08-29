"""事件三选一 mod。"""

from __future__ import annotations

import logging
import time

from vision_bot.core.input import Mouse
from vision_bot.perception.snapshot import ScreenSnapshot, snap
from vision_bot.runtime.context import RunContext
from vision_bot.runtime.result import Result

logger = logging.getLogger(__name__)

DETECT: set[str] = {
    "choice.fei_fei",
    "choice.shi_chang_shi",
    "choice.mo_zi",
}

_PRIORITY = (
    ("choice.fei_fei", "fei_fei"),
    ("choice.shi_chang_shi", "shi_chang_shi"),
    ("choice.mo_zi", "mo_zi"),
)


def detect(shot: ScreenSnapshot, ctx: RunContext | None = None) -> str | None:
    if any(shot.found(k) for k in ("choice.fei_fei", "choice.shi_chang_shi", "choice.mo_zi")):
        return "qldq.battle_hub.pick_event.choose"
    return None


def relocate(ctx: RunContext) -> str | None:
    shot = snap(DETECT)
    return detect(shot, ctx)


def choose(ctx) -> Result:
    shot = snap(DETECT)
    for key, outcome in _PRIORITY:
        c = shot.center(key)
        if c:
            Mouse().move(*c).click().sleep(0.2).perform()
            ctx.vars["pending_event"] = outcome
            logger.info("pick_event 选中 %s", outcome)
            ctx.goto("qldq.battle_hub.pick_event.verify")
            return Result.success()
    return Result.fail("无事件选项")


def verify(ctx) -> Result:
    outcome = ctx.vars.get("pending_event")
    if not outcome:
        return Result.fail("无 pending 事件")
    key = next(k for k, o in _PRIORITY if o == outcome)
    time.sleep(0.6)
    shot = snap({key})
    if shot.found(key):
        ctx.goto("qldq.battle_hub.pick_event.choose")
        return Result.success()
    ctx.vars.pop("pending_event", None)
    ctx.goto(f"qldq.{outcome}")
    return Result.success()
