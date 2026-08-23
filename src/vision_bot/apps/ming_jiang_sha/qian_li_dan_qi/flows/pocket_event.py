"""锦囊事件（简化）。"""

from __future__ import annotations

import logging
import random

from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.detect import qmod, relocate_pocket_event
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.signals import snap_center, snap_found
from vision_bot.core.input import Mouse
from vision_bot.core.vision import find_all_images
from vision_bot.runtime.builders import flow, mod
from vision_bot.runtime.flow import Flow
from vision_bot.runtime.result import Result

logger = logging.getLogger(__name__)

_CHECK_SIGNALS = {"fight.cancel", "pocket.ok"}


def _pick(ctx) -> Result:
    base = ctx.base_dir / "data/ming_jiang_sha/qian_li_dan_qi/pocket_event/event_patterm.png"
    hits = find_all_images(base, threshold=0.8, max_count=16)
    if not hits:
        ctx.goto(qmod("pocket_event", "check"))
        return Result.success()
    hit = random.choice(hits)
    if hit.center:
        Mouse().move(*hit.center).click().sleep(0.4).perform()
    ctx.goto(qmod("pocket_event", "check"))
    return Result.success()


def _check(ctx) -> Result:
    snap = ctx.snap(_CHECK_SIGNALS)
    if snap_found(snap, "fight.cancel"):
        ctx.goto("qldq.fight")
        return Result.success()
    if snap_found(snap, "pocket.ok"):
        return Result.success()
    return Result.success()


def _click_ok(ctx) -> Result:
    snap = ctx.snap({"pocket.ok"})
    c = snap_center(snap, "pocket.ok")
    if c:
        Mouse().move(*c).click().sleep(0.3).perform()
    ctx.goto(qmod("pocket_event", "check"))
    return Result.success()


def build() -> Flow:
    return flow(
        "qldq.pocket_event",
        "锦囊",
        children=[
            mod("qldq.pocket_event.pick", "选锦囊", _pick),
            mod("qldq.pocket_event.check", "检查", _check),
            mod("qldq.pocket_event.click_ok", "点确定", _click_ok),
        ],
        relocate=[relocate_pocket_event],
    )
