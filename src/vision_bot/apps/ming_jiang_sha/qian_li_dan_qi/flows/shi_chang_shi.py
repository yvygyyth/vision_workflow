"""十常侍：连点攻击直到进战（出现取消），再走无赠礼战斗。"""

from __future__ import annotations

import logging
import time

from vision_bot.actions import click, do, move
from vision_bot.apps.ming_jiang_sha.paths import QLDQ
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.flows import fight
from vision_bot.runtime.context import RunContext
from vision_bot.runtime.relocate import RelocateRule
from vision_bot.runtime.result import Result
from vision_bot.vision import find, snap

logger = logging.getLogger(__name__)

_ATTACK = f"{QLDQ}/shi_chang_shi/attack.png"
_CANCEL = f"{QLDQ}/fight/cancel.png"

DETECT: set[str] = {_ATTACK, _CANCEL}


def _shot(ctx: RunContext):
    return snap(DETECT)


relocate: list[RelocateRule] = [
    RelocateRule(
        when=lambda ctx: _shot(ctx).found(_ATTACK),
        then="qldq.shi_chang_shi.attack",
    ),
    RelocateRule(
        when=lambda ctx: _shot(ctx).found(_CANCEL),
        then="qldq.shi_chang_shi.check_cancel",
    ),
]


def attack(ctx) -> Result:
    result = find(_ATTACK, timeout=1.5)
    if not result.ok or not result.value.center:
        # 攻击暂时没了：交给 check 等取消或再打
        logger.info("attack → 无 attack，转检查取消")
        return Result.success(then="qldq.shi_chang_shi.check_cancel")
    cx, cy = result.value.center
    for _ in range(5):
        do(move().to(cx, cy).raw(), click())()
        time.sleep(0.12)
    return Result.success(then="qldq.shi_chang_shi.check_cancel")


def check_cancel(ctx) -> Result:
    # 移开鼠标，避免 tooltip 挡住随后出现的取消
    do(move().to(80, 80))()
    # 点完攻击后取消可能稍晚才出
    if find(_CANCEL, timeout=3.0, interval=0.3).ok:
        logger.info("shi_chang_shi → 已进战，无赠礼战斗")
        return fight.run_battle_no_gift(ctx)
    if find(_ATTACK, timeout=1.0).ok:
        return Result.success(then="qldq.shi_chang_shi.attack")
    return Result.fail("十常侍：无攻击且未出现取消")
