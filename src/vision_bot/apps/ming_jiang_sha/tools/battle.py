"""名将杀共用：纯战斗工具 Flow（点取消 → … → 本轮结束判定）。"""

from __future__ import annotations

import logging

from vision_bot.actions import click, do, move
from vision_bot.apps.ming_jiang_sha.paths import COMMON_DIR, QLDQ
from vision_bot.runtime.builders import flow, mod
from vision_bot.runtime.context import RunContext
from vision_bot.runtime.flow import Flow
from vision_bot.runtime.relocate import RelocateRule
from vision_bot.runtime.result import Result
from vision_bot.vision import ScreenSnapshot, find, snap

logger = logging.getLogger(__name__)

# 八王等模式也复用千里单骑战斗 UI 模板
_FIGHT = f"{QLDQ}/fight"
CANCEL = f"{_FIGHT}/cancel.png"
SETTING = f"{_FIGHT}/setting.png"
CHALLENGE_END = f"{_FIGHT}/challenge_end.png"
NEXT_STEP = f"{_FIGHT}/next_step.png"
AUTO = f"{_FIGHT}/auto.png"
CONFIRM = f"{COMMON_DIR}/confirm.png"

RUN_ENDED_FLAG = "mjs_battle_run_ended"

DETECT: set[str] = {CANCEL, SETTING, CHALLENGE_END, NEXT_STEP}


def _battle_shot(ctx: RunContext) -> ScreenSnapshot:
    return snap(DETECT)


relocate: list[RelocateRule] = [
    RelocateRule(
        when=lambda ctx: _battle_shot(ctx).found(CANCEL),
        then="mjs.battle.click_cancel",
    ),
    RelocateRule(
        when=lambda ctx: _battle_shot(ctx).found(SETTING),
        then="mjs.battle.click_setting",
    ),
    RelocateRule(
        when=lambda ctx: _battle_shot(ctx).found(CHALLENGE_END),
        then="mjs.battle.wait_end",
    ),
    RelocateRule(
        when=lambda ctx: _battle_shot(ctx).found(NEXT_STEP),
        then="mjs.battle.next_step",
    ),
]


def click_cancel(ctx) -> Result:
    # 识别/点击取消前移开鼠标，防止挡住图标
    do(move().to(80, 80))()
    return do(move().image(CANCEL), click().pause(0.2))()


def click_setting(ctx) -> Result:
    return do(move().image(SETTING), click().pause(0.5))()


def click_auto(ctx) -> Result:
    return do(move().image(AUTO).match(timeout=1.0), click().pause(0.2))()


def wait_end(ctx) -> Result:
    return do(
        move().image(CHALLENGE_END).match(timeout=1200, interval=5),
        click().pause(0.2),
    )()


def next_step(ctx) -> Result:
    for _ in range(5):
        r = do(move().image(NEXT_STEP).match(timeout=1.2), click().pause(0.4))()
        if not r.ok:
            break
    return Result.success()


def check_run_end(ctx) -> Result:
    """本轮彻底结束则打标，由各模式外壳自行 goto 结算/结束。"""
    if find(CONFIRM, timeout=1.0, threshold=0.8).ok:
        logger.info("mjs.battle check_run_end → 标记本轮结束")
        ctx.vars[RUN_ENDED_FLAG] = True
    return Result.success()


def build_battle() -> Flow:
    """名将杀共用纯战斗工具（RunConfig.tools 默认挂载，供 call）。"""
    return flow(
        id="mjs.battle",
        name="纯战斗",
        relocate=relocate,
        children=[
            mod(id="mjs.battle.click_cancel", name="点取消", active=click_cancel),
            mod(id="mjs.battle.click_setting", name="点设置", active=click_setting),
            mod(id="mjs.battle.click_auto", name="点自动", active=click_auto),
            mod(id="mjs.battle.wait_end", name="等结束", active=wait_end),
            mod(id="mjs.battle.next_step", name="下一步", active=next_step),
            mod(
                id="mjs.battle.check_run_end",
                name="本轮结束判定",
                active=check_run_end,
            ),
        ],
    )
