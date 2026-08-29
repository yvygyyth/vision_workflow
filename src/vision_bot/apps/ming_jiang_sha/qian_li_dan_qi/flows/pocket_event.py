"""锦囊 mod。"""

from __future__ import annotations

import random

from vision_bot.apps.ming_jiang_sha.paths import QLDQ
from vision_bot.core.input import Mouse
from vision_bot.perception.session import perception
from vision_bot.perception.snapshot import snap
from vision_bot.runtime.context import RunContext
from vision_bot.runtime.result import Result
from vision_bot.vision import find_all

_PATTERN = f"{QLDQ}/pocket_event/event_patterm.png"
_OK = f"{QLDQ}/pocket_event/ok.png"
_CANCEL = f"{QLDQ}/fight/cancel.png"
_CHECK = {_CANCEL, _OK}


def relocate(ctx: RunContext) -> str | None:
    return "qldq.pocket_event.check"


def pick(ctx) -> Result:
    base = perception().base_dir / _PATTERN
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
    shot = snap(_CHECK)
    if shot.found(_CANCEL):
        ctx.goto("qldq.fight")
    return Result.success()


def click_ok(ctx) -> Result:
    shot = snap({_OK})
    c = shot.center(_OK)
    if c:
        Mouse().move(*c).click().sleep(0.3).perform()
    ctx.goto("qldq.pocket_event.check")
    return Result.success()
