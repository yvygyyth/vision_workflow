"""锦囊 mod。"""

from __future__ import annotations

import random

from vision_bot.apps.ming_jiang_sha.paths import QLDQ
from vision_bot.core.input import Mouse
from vision_bot.perception.signal import Signal
from vision_bot.runtime.context import RunContext
from vision_bot.runtime.result import Result
from vision_bot.vision import find_all

_DIR = f"{QLDQ}/pocket_event"

SIGNALS: dict[str, Signal] = {
    "pocket.event_pattern": Signal(template=f"{_DIR}/event_patterm.png"),
    "pocket.ok": Signal(template=f"{_DIR}/ok.png"),
}

_CHECK_SIGNALS = {"fight.cancel", "pocket.ok"}


def relocate(ctx: RunContext) -> str | None:
    return "qldq.pocket_event.check"


def pick(ctx) -> Result:
    base = ctx.base_dir / f"{_DIR}/event_patterm.png"
    hits = find_all(base, threshold=0.8, max_count=16)
    if not hits.ok:
        ctx.goto("qldq.pocket_event.check")
        return Result.success()
    hit = random.choice(hits.value)
    if hit.center:
        Mouse().move(*hit.center).click().sleep(0.4).perform()
    ctx.goto("qldq.pocket_event.check")
    return Result.success()


def check(ctx) -> Result:
    snap = ctx.snap(_CHECK_SIGNALS)
    if snap.found("fight.cancel"):
        ctx.goto("qldq.fight")
        return Result.success()
    if snap.found("pocket.ok"):
        return Result.success()
    return Result.success()


def click_ok(ctx) -> Result:
    snap = ctx.snap({"pocket.ok"})
    c = snap.center("pocket.ok")
    if c:
        Mouse().move(*c).click().sleep(0.3).perform()
    ctx.goto("qldq.pocket_event.check")
    return Result.success()
