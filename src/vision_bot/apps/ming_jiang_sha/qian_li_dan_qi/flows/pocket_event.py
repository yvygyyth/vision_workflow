"""锦囊 mod。

刚进必是 ``_PATTERN``（通常 3 张），由 ``enter`` 直接点。
点完后 ``check`` 分流（先挪鼠标再轮询，避免过渡帧 / tooltip 误判）：
1. ``_PATTERN`` → 再选一张
2. ``_OK`` → 当场点确定
3. ``_CANCEL`` → 进入无赠礼战斗
4. ``battle_interface`` → 已回三选一
"""

from __future__ import annotations

import logging
import random
import time

from vision_bot.actions import click, do, move
from vision_bot.apps.ming_jiang_sha.paths import QLDQ
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.flows import fight
from vision_bot.runtime.context import RunContext
from vision_bot.runtime.relocate import RelocateRule
from vision_bot.runtime.result import Result
from vision_bot.vision import find_all, snap

logger = logging.getLogger(__name__)

_PATTERN = f"{QLDQ}/pocket_event/event_patterm.png"
_OK = f"{QLDQ}/pocket_event/ok.png"
_CANCEL = f"{QLDQ}/fight/cancel.png"
_BATTLE_INTERFACE = f"{QLDQ}/enter_battle/battle_interface.png"

DETECT: set[str] = {_PATTERN, _OK, _CANCEL, _BATTLE_INTERFACE}


def _shot(ctx: RunContext | None = None):
    return snap(DETECT)


relocate: list[RelocateRule] = [
    RelocateRule(
        when=lambda ctx: _shot().found(_PATTERN),
        then="qldq.pocket_event.enter",
    ),
    RelocateRule(
        when=lambda ctx: _shot().found(_OK) or _shot().found(_CANCEL),
        then="qldq.pocket_event.check",
    ),
    RelocateRule(
        when=lambda ctx: _shot().found(_BATTLE_INTERFACE),
        then="qldq.battle_hub",
    ),
]


def enter(ctx) -> Result:
    """进店首点：只找锦囊图案。"""
    return _click_pattern(ctx)


def check(ctx) -> Result:
    # 先挪开：点完锦囊光标常还在牌上，会挡 OK / 取消
    do(move().to(80, 80))()
    deadline = time.monotonic() + 4.0
    while time.monotonic() < deadline:
        shot = _shot()
        if shot.found(_OK):
            do(move().image(_OK).match(timeout=0.8), click().pause(0.3))()
            return Result.success(then="qldq.pocket_event.check")
        if shot.found(_PATTERN):
            return Result.success(then="qldq.pocket_event.enter")
        if shot.found(_BATTLE_INTERFACE):
            logger.info("pocket_event → 三选一")
            return Result.success(then="qldq.battle_hub")
        if shot.found(_CANCEL):
            logger.info("pocket_event → 无赠礼战斗")
            return fight.run_battle_no_gift(ctx)
        time.sleep(0.25)
    return Result.fail("锦囊画面未识别")


def _click_pattern(ctx) -> Result:
    """场上通常 3 张 ``_PATTERN``；识别到几张点随机一张即可。"""
    hits = find_all(_PATTERN, threshold=0.8, max_count=3)
    if not hits.ok or not hits.value:
        return Result.success(then="qldq.pocket_event.check")
    choices = [h for h in hits.value if h.center] or list(hits.value)
    hit = random.choice(choices)
    logger.info("pocket_event 锦囊候选=%s，点其中一张", len(choices))
    if hit.center:
        do(move().to(*hit.center).raw(), click().pause(0.35))()
    return Result.success(then="qldq.pocket_event.check")
