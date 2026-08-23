"""十常侍 → confirm 后进战斗。"""

from __future__ import annotations

import logging

from vision_bot.actions import click, do, move
from vision_bot.apps.ming_jiang_sha.actions import click_confirm, module_confirm
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.detect import relocate_shi_chang_shi
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.signals import snap_found
from vision_bot.runtime.flow import Flow, StepResult
from vision_bot.runtime.types import END, FAIL, FIGHT

logger = logging.getLogger(__name__)


def _attack(ctx) -> StepResult:
    act = ctx.action_ctx()
    hit = act.find("data/ming_jiang_sha/qian_li_dan_qi/shi_chang_shi/attack.png", timeout=0.8)
    if hit.found and hit.center:
        for _ in range(5):
            do(move().to(*hit.center).raw(), click())(act)
        return StepResult.ok(next_id="check_cancel")
    return StepResult.fail("无 attack")


def _check_cancel(ctx) -> StepResult:
    snap = ctx.snap({"fight.cancel"})
    if snap_found(snap, "fight.cancel"):
        r = click_confirm(ctx.action_ctx())
        if r.failed:
            return StepResult.fail(r.message)
        return StepResult.end(FIGHT)
    return StepResult.ok(next_id="attack")


def build() -> Flow:
    return Flow(
        id="shi_chang_shi",
        name="十常侍",
        entry="confirm",
        relocate=relocate_shi_chang_shi,
        steps={
            "confirm": module_confirm,
            "attack": _attack,
            "check_cancel": _check_cancel,
        },
        routes={"confirm": {FAIL: "attack"}},
        on={FIGHT: END},
    )
