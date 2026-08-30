"""名将杀共用：纯战斗工具 Flow（先取消 → 设置 → 自动 → … → 本轮结束判定）。"""

from __future__ import annotations

import logging
import time

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
# 进战 setting 会先出现，但必须先点掉 cancel 后点 setting 才能出 auto
_CANCEL_DONE = "mjs_battle_cancel_done"

DETECT: set[str] = {CANCEL, SETTING, CHALLENGE_END, NEXT_STEP}


def _battle_shot(ctx: RunContext) -> ScreenSnapshot:
    return snap(DETECT)


def _cancel_done(ctx: RunContext) -> bool:
    return bool(ctx.vars.get(_CANCEL_DONE))


relocate: list[RelocateRule] = [
    RelocateRule(
        when=lambda ctx: _battle_shot(ctx).found(CANCEL),
        then="mjs.battle.click_cancel",
    ),
    # 仅「已点过取消」后才允许因 setting 跳到点设置（避免进战 setting 先出现就误点）
    RelocateRule(
        when=lambda ctx: _cancel_done(ctx) and _battle_shot(ctx).found(SETTING),
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
    # 进战默认：先移开鼠标并等取消（setting 先出也不跳设置）
    RelocateRule(when=lambda ctx: True, then="mjs.battle.click_cancel"),
]


def click_cancel(ctx) -> Result:
    ctx.vars.pop(_CANCEL_DONE, None)
    # 先挪开鼠标：开局光标常触发 tooltip，会挡住随后出现的取消
    do(move().to(80, 80))()
    time.sleep(0.3)
    r = do(
        move().image(CANCEL).match(timeout=20.0, interval=0.4),
        click().pause(0.2),
    )()
    if r.ok:
        ctx.vars[_CANCEL_DONE] = True
    return r


def click_setting(ctx) -> Result:
    return do(move().image(SETTING).match(timeout=5.0), click().pause(0.5))()


def click_auto(ctx) -> Result:
    # 找不到自动也不整段失败纠偏（菜单已关 / 已是自动态）
    r = do(move().image(AUTO).match(timeout=2.0), click().pause(0.2))()
    if not r.ok:
        logger.info("click_auto → 未找到 auto，继续等结束")
        return Result.success()
    return r


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
    """本轮彻底结束则打标，由各模式外壳自行跳转结算/结束。"""
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
