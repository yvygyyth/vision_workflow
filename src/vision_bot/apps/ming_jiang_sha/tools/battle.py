"""名将杀共用：纯战斗工具 Flow（先取消 → 设置 → 自动 → 等结束 → 下一步）。"""

from __future__ import annotations

import logging
import time

from vision_bot.actions import click, do, move
from vision_bot.apps.ming_jiang_sha.actions import click_confirm
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

_RELOCATE_SHOT = "_mjs_battle_relocate_shot"
_CONFIRM_THRESHOLD = 0.6

DETECT: set[str] = {CONFIRM, CANCEL, SETTING, CHALLENGE_END, NEXT_STEP}


def _move_aside() -> None:
    """开局光标常触发 tooltip，会挡住随后出现的取消。"""
    do(move().to(80, 80))()


def _confirm_visible() -> bool:
    return find(CONFIRM, timeout=0.0, threshold=_CONFIRM_THRESHOLD).ok


def _clear_confirms(*, max_clicks: int = 4) -> bool:
    """点掉连续确认框，并验证已消失。返回是否干净。"""
    for i in range(max_clicks):
        if not _confirm_visible():
            return True
        logger.info("mjs.battle 清确认 #%s", i + 1)
        click_confirm(pause=0.25)
        time.sleep(0.25)
    if _confirm_visible():
        logger.warning("mjs.battle 确认仍在")
        return False
    return True


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


# 确认优先于取消：弹窗挡住时不能硬点取消。
# 进战 setting 会先出现，但点设置前必须先点取消；故 relocate 绝不因 setting 跳过取消。
# 正常顺序靠 children：点取消 → 点设置 → 点自动 → …
relocate: list[RelocateRule] = [
    RelocateRule(when=_prepare_relocate, then=None),
    RelocateRule(
        when=lambda ctx: _battle_shot(ctx).found(CONFIRM),
        then="mjs.battle.dismiss_confirm",
    ),
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


def dismiss_confirm(ctx) -> Result:
    ctx.vars.pop(_RELOCATE_SHOT, None)
    if not _clear_confirms():
        return Result.fail("确认框未清除")
    logger.info("mjs.battle dismiss_confirm → 确认已清")
    return Result.success()


def click_cancel(ctx) -> Result:
    ctx.vars.pop(_RELOCATE_SHOT, None)
    # relocate 已挪过一次；这里再挪一次兜底（例如纠偏直达本步）
    _move_aside()
    r = do(
        move().image(CANCEL).match(timeout=12.0, interval=0.25),
        click().pause(0.15),
    )()
    if not r.ok:
        return r
    # 点取消后常连出确认
    if not _clear_confirms():
        return Result.fail("点取消后确认框未清除")
    return Result.success()


def click_setting(ctx) -> Result:
    return do(move().image(SETTING).match(timeout=4.0, interval=0.25), click().pause(0.35))()


def click_auto(ctx) -> Result:
    r = do(move().image(AUTO).match(timeout=1.5, interval=0.25), click().pause(0.15))()
    if not r.ok:
        logger.info("click_auto → 未找到 auto，继续等结束")
        return Result.success()
    return r


def wait_end(ctx) -> Result:
    """等挑战结束；等待期间顺手清确认，避免弹窗卡住识图。"""
    deadline = time.monotonic() + 1200.0
    while time.monotonic() < deadline:
        ctx.check_cancelled()
        _clear_confirms(max_clicks=2)
        r = do(
            move().image(CHALLENGE_END).match(timeout=5.0, interval=0.5),
            click().pause(0.2),
        )()
        if r.ok:
            return r
    return Result.fail("等结束超时")


def next_step(ctx) -> Result:
    for _ in range(5):
        r = do(move().image(NEXT_STEP).match(timeout=1.2), click().pause(0.4))()
        if not r.ok:
            break
        _clear_confirms(max_clicks=2)
    if not _clear_confirms():
        return Result.fail("下一步后确认框未清除")
    return Result.success()


def build_battle() -> Flow:
    """名将杀共用纯战斗工具（RunConfig.tools 默认挂载，供 call）。"""
    return flow(
        id="mjs.battle",
        name="纯战斗",
        relocate=relocate,
        children=[
            mod(id="mjs.battle.dismiss_confirm", name="清确认", active=dismiss_confirm),
            mod(id="mjs.battle.click_cancel", name="点取消", active=click_cancel),
            mod(id="mjs.battle.click_setting", name="点设置", active=click_setting),
            mod(id="mjs.battle.click_auto", name="点自动", active=click_auto),
            mod(id="mjs.battle.wait_end", name="等结束", active=wait_end),
            mod(id="mjs.battle.next_step", name="下一步", active=next_step),
        ],
    )
