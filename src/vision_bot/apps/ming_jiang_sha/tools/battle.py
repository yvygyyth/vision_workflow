"""名将杀共用：纯战斗工具 Flow（先取消 → 设置 → 自动 → 等结束 → 下一步）。"""

from __future__ import annotations

import logging
import time

from vision_bot.actions import click, do, move
from vision_bot.apps.ming_jiang_sha.paths import QLDQ
from vision_bot.runtime.builders import flow, mod
from vision_bot.runtime.context import RunContext
from vision_bot.runtime.flow import Flow
from vision_bot.runtime.relocate import RelocateRule
from vision_bot.runtime.result import Result
from vision_bot.vision import ScreenSnapshot, snap

logger = logging.getLogger(__name__)

# 八王等模式也复用千里单骑战斗 UI 模板
_FIGHT = f"{QLDQ}/fight"
CANCEL = f"{_FIGHT}/cancel.png"
SETTING = f"{_FIGHT}/setting.png"
CHALLENGE_END = f"{_FIGHT}/challenge_end.png"
NEXT_STEP = f"{_FIGHT}/next_step.png"
AUTO = f"{_FIGHT}/auto.png"

_RELOCATE_SHOT = "_mjs_battle_relocate_shot"

DETECT: set[str] = {CANCEL, SETTING, CHALLENGE_END, NEXT_STEP}


def _move_aside() -> None:
    """开局光标常触发 tooltip，会挡住随后出现的取消。"""
    do(move().to(80, 80))()


def _prepare_relocate(ctx: RunContext) -> bool:
    """relocate 第一条：先挪鼠标，再只识图一次供后续规则用（本条不命中）。"""
    _move_aside()
    time.sleep(0.12)
    ctx.vars[_RELOCATE_SHOT] = snap(DETECT)
    return False


def _battle_shot(ctx: RunContext) -> ScreenSnapshot:
    shot = ctx.vars.get(_RELOCATE_SHOT)
    if isinstance(shot, ScreenSnapshot):
        return shot
    return snap(DETECT)


# 进战 setting 会先出现，但点设置前必须先点取消；故 relocate 绝不因 setting 跳过取消。
# 正常顺序靠 children：点取消 → 点设置 → 点自动 → …
relocate: list[RelocateRule] = [
    RelocateRule(when=_prepare_relocate, then=None),
    RelocateRule(
        when=lambda ctx: _battle_shot(ctx).found(CANCEL),
        then="mjs.battle.click_cancel",
    ),
    RelocateRule(
        when=lambda ctx: _battle_shot(ctx).found(CHALLENGE_END),
        then="mjs.battle.wait_end",
    ),
    RelocateRule(
        when=lambda ctx: _battle_shot(ctx).found(NEXT_STEP),
        then="mjs.battle.next_step",
    ),
    # setting 先出 / 尚未出现取消：仍从点取消开跑
    RelocateRule(when=lambda ctx: True, then="mjs.battle.click_cancel"),
]


def click_cancel(ctx) -> Result:
    ctx.vars.pop(_RELOCATE_SHOT, None)
    # relocate 已挪过一次；这里再挪一次兜底（例如纠偏直达本步）
    _move_aside()
    return do(
        move().image(CANCEL).match(timeout=12.0, interval=0.25),
        click().pause(0.15),
    )()


def click_setting(ctx) -> Result:
    return do(move().image(SETTING).match(timeout=4.0, interval=0.25), click().pause(0.35))()


def click_auto(ctx) -> Result:
    r = do(move().image(AUTO).match(timeout=1.5, interval=0.25), click().pause(0.15))()
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
    """点掉仍在的下一步；找不到则直接成功，由外壳去做结算。"""
    clicked = 0
    for _ in range(5):
        r = do(move().image(NEXT_STEP).match(timeout=1.2), click().pause(0.4))()
        if not r.ok:
            break
        clicked += 1
    logger.info("next_step → 已点%s次，无下一步，交外壳结算", clicked)
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
        ],
    )
