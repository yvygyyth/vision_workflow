"""事件三选一 mod。"""

from __future__ import annotations

import logging
import time

from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.flows.battle_hub import (
    CHOICE_REGION,
    FEI_FEI,
    MO_ZI,
    SHI_CHANG_SHI,
)
from vision_bot.core.input import Mouse
from vision_bot.vision import ScreenSnapshot, snap
from vision_bot.runtime.context import RunContext
from vision_bot.runtime.relocate import RelocateRule
from vision_bot.runtime.result import Result

logger = logging.getLogger(__name__)

DETECT: set[str] = {FEI_FEI, SHI_CHANG_SHI, MO_ZI}

_PRIORITY = (
    (FEI_FEI, "fei_fei"),
    (SHI_CHANG_SHI, "shi_chang_shi"),
    (MO_ZI, "mo_zi"),
)


def _has_event_choice(ctx: RunContext) -> bool:
    shot = snap(DETECT, region=CHOICE_REGION)
    return any(shot.found(p) for p in DETECT)


relocate: list[RelocateRule] = [
    RelocateRule(when=_has_event_choice, then="qldq.battle_hub.pick_event.choose"),
]


def choose(ctx) -> Result:
    shot = snap(DETECT, region=CHOICE_REGION)
    for path, outcome in _PRIORITY:
        c = shot.center(path)
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
    path = next(p for p, o in _PRIORITY if o == outcome)
    time.sleep(0.6)
    shot = snap(path, region=CHOICE_REGION)
    if shot.ok:
        ctx.goto("qldq.battle_hub.pick_event.choose")
        return Result.success()
    ctx.vars.pop("pending_event", None)
    ctx.goto(f"qldq.{outcome}")
    return Result.success()
