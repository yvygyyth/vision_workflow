"""锦囊事件（简化）。"""

from __future__ import annotations

import logging
import random

from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.detect import relocate_pocket_event
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.signals import snap_center, snap_found
from vision_bot.core.input import Mouse
from vision_bot.core.vision import find_all_images
from vision_bot.runtime.flow import Flow, StepResult
from vision_bot.runtime.types import BACK_TO_HUB, END, FIGHT

logger = logging.getLogger(__name__)

_CHECK_SIGNALS = {"fight.cancel", "pocket.ok"}


def _pick(ctx) -> StepResult:
    base = ctx.base_dir / "data/ming_jiang_sha/qian_li_dan_qi/pocket_event/event_patterm.png"
    hits = find_all_images(base, threshold=0.8, max_count=16)
    if not hits:
        return StepResult.ok(next_id="check")
    hit = random.choice(hits)
    if hit.center:
        Mouse().move(*hit.center).click().sleep(0.4).perform()
    return StepResult.ok(next_id="check")


def _check(ctx) -> StepResult:
    snap = ctx.snap(_CHECK_SIGNALS)
    if snap_found(snap, "fight.cancel"):
        return StepResult.end(FIGHT)
    if snap_found(snap, "pocket.ok"):
        return StepResult.ok(next_id="click_ok")
    return StepResult.end(BACK_TO_HUB)


def _click_ok(ctx) -> StepResult:
    snap = ctx.snap({"pocket.ok"})
    c = snap_center(snap, "pocket.ok")
    if c:
        Mouse().move(*c).click().sleep(0.3).perform()
    return StepResult.ok(next_id="check")


def build() -> Flow:
    return Flow(
        id="pocket_event",
        name="锦囊",
        entry="pick",
        relocate=relocate_pocket_event,
        steps={
            "pick": _pick,
            "check": _check,
            "click_ok": _click_ok,
        },
        on={FIGHT: END, BACK_TO_HUB: END},
    )
