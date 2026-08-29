"""十常侍 mod。"""

from __future__ import annotations

from vision_bot.actions import click, do, move
from vision_bot.apps.ming_jiang_sha.actions import click_confirm
from vision_bot.apps.ming_jiang_sha.paths import QLDQ
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.flows import fight
from vision_bot.vision import find, snap
from vision_bot.runtime.context import RunContext
from vision_bot.runtime.relocate import RelocateRule
from vision_bot.runtime.result import Result

_ATTACK = f"{QLDQ}/shi_chang_shi/attack.png"
_CANCEL = f"{QLDQ}/fight/cancel.png"


def _has_attack(ctx: RunContext) -> bool:
    return snap({_ATTACK, _CANCEL}).found(_ATTACK)


relocate: list[RelocateRule] = [
    RelocateRule(when=_has_attack, then="qldq.shi_chang_shi.attack"),
]


def attack(ctx) -> Result:
    result = find(_ATTACK, timeout=0.8)
    if not result.ok or not result.value.center:
        return Result.fail("无 attack")
    for _ in range(5):
        do(move().to(*result.value.center).raw(), click())()
    ctx.goto("qldq.shi_chang_shi.check_cancel")
    return Result.success()


def check_cancel(ctx) -> Result:
    if snap(_CANCEL).ok:
        r = click_confirm()
        if not r.ok:
            return r
        return fight.run_battle_no_gift(ctx)
    ctx.goto("qldq.shi_chang_shi.attack")
    return Result.success()
