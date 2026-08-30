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
SETTING2 = f"{_FIGHT}/setting2.png"
CHALLENGE_END = f"{_FIGHT}/challenge_end.png"
NEXT_STEP = f"{_FIGHT}/next_step.png"
AUTO = f"{_FIGHT}/auto.png"

_RELOCATE_SHOT = "_mjs_battle_relocate_shot"

DETECT: set[str] = {CANCEL, SETTING, SETTING2, CHALLENGE_END, NEXT_STEP}


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


def _in_setup(ctx: RunContext) -> bool:
    """设置/取消还在 → 仍处开局，不得跳到等结束/下一步。"""
    shot = _battle_shot(ctx)
    return shot.found(CANCEL) or shot.found(SETTING) or shot.found(SETTING2)


def _setting_expanded() -> bool:
    """setting2 = 菜单已展开（才能看见 auto）。"""
    return snap(SETTING2).ok


def _ensure_setting_open() -> bool:
    """保证设置菜单展开；已展开则绝不再点 setting（会收起）。"""
    if _setting_expanded():
        return True
    r = do(move().image(SETTING).match(timeout=2.0, interval=0.25), click().pause(0.35))()
    if not r.ok:
        return False
    time.sleep(0.2)
    return _setting_expanded()


# 进战 setting 常先出，但点设置前必须先点取消。
# 有 cancel/setting 时绝不因误匹配 challenge_end/next_step 跳过取消。
relocate: list[RelocateRule] = [
    RelocateRule(when=_prepare_relocate, then=None),
    RelocateRule(
        when=lambda ctx: _battle_shot(ctx).found(CANCEL),
        then="mjs.battle.click_cancel",
    ),
    RelocateRule(
        when=lambda ctx: _battle_shot(ctx).found(SETTING)
        or _battle_shot(ctx).found(SETTING2),
        then="mjs.battle.click_cancel",
    ),
    RelocateRule(
        when=lambda ctx: not _in_setup(ctx) and _battle_shot(ctx).found(CHALLENGE_END),
        then="mjs.battle.wait_end",
    ),
    RelocateRule(
        when=lambda ctx: not _in_setup(ctx) and _battle_shot(ctx).found(NEXT_STEP),
        then="mjs.battle.next_step",
    ),
    RelocateRule(when=lambda ctx: True, then="mjs.battle.click_cancel"),
]


def click_cancel(ctx) -> Result:
    ctx.vars.pop(_RELOCATE_SHOT, None)
    _move_aside()
    r = do(
        move().image(CANCEL).match(timeout=12.0, interval=0.25),
        click().pause(0.2),
    )()
    if not r.ok:
        logger.warning("click_cancel → 未找到取消")
    return r


def click_setting(ctx) -> Result:
    if _setting_expanded():
        logger.info("click_setting → 已展开(setting2)，跳过点击")
        return Result.success()
    r = do(move().image(SETTING).match(timeout=4.0, interval=0.25), click().pause(0.35))()
    if not r.ok:
        return r
    if not _setting_expanded():
        logger.warning("click_setting → 点击后未见 setting2")
    return r


def _try_click_auto(*, timeout: float) -> Result:
    return do(move().image(AUTO).match(timeout=timeout, interval=0.25), click().pause(0.15))()


def click_auto(ctx) -> Result:
    r = _try_click_auto(timeout=1.5)
    if r.ok:
        return r

    # 无 auto：先看是否已展开；未展开才点 setting，已展开则疑似没点取消
    if _setting_expanded():
        logger.info("click_auto → 已展开但无 auto，补点取消后再找")
        _move_aside()
        cancel_r = do(
            move().image(CANCEL).match(timeout=3.0, interval=0.25),
            click().pause(0.25),
        )()
        if cancel_r.ok:
            # 取消后菜单可能还开着：只在未展开时才点 setting，避免点第二次收起
            if not _ensure_setting_open():
                logger.info("click_auto → 补取消后无法展开 setting")
            r2 = _try_click_auto(timeout=2.0)
            if r2.ok:
                return r2
    else:
        logger.info("click_auto → 未展开，尝试展开 setting 后再找 auto")
        if _ensure_setting_open():
            r2 = _try_click_auto(timeout=2.0)
            if r2.ok:
                return r2

    logger.info("click_auto → 仍无 auto，继续等结束")
    return Result.success()


def wait_end(ctx) -> Result:
    # interval 别太大：结束按钮出来后要尽快点，否则后面 next_step 会「假成功」
    return do(
        move().image(CHALLENGE_END).match(timeout=1200, interval=0.8),
        click().pause(0.35),
    )()


def next_step(ctx) -> Result:
    """点掉下一步。结束点完后下一步常晚几秒才出，首轮要等够；点完再交外壳结算。"""
    clicked = 0
    # 首轮久等出现；之后短轮询点到消失
    timeouts = (12.0,) + (1.5,) * 8
    for timeout in timeouts:
        r = do(
            move().image(NEXT_STEP).match(timeout=timeout, interval=0.35),
            click().pause(0.4),
        )()
        if not r.ok:
            break
        clicked += 1
    if clicked == 0:
        logger.info("next_step → 等待后仍无下一步，交外壳结算")
    else:
        logger.info("next_step → 已点%s次，交外壳结算", clicked)
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
