"""活动领取。"""

from __future__ import annotations

from vision_bot.actions import click, do, move
from vision_bot.apps.ming_jiang_sha.actions import step_go_back, step_space_close
from vision_bot.apps.ming_jiang_sha.flow_helpers import do_click, scroll_center
from vision_bot.apps.ming_jiang_sha.paths import DATA_ROOT
from vision_bot.runtime.flow import Flow, StepResult

_DIR = f"{DATA_ROOT}/actaivity"


def _bu_gua_wait(ctx) -> StepResult:
    ctx.sleep(3.0)
    do(move().to(1400, 600).raw(), click())(ctx.action_ctx())
    return StepResult.ok()


def _bu_gua_click(ctx) -> StepResult:
    do(move().to(1400, 600).raw(), click())(ctx.action_ctx())
    return StepResult.ok()


DONE = "activity_done"


def _finish(ctx) -> StepResult:
    step_go_back(ctx)
    return StepResult.end(DONE)


def build() -> Flow:
    return Flow(
        id="activity",
        name="活动",
        entry="entry",
        steps={
            "entry": lambda ctx: do_click(ctx, f"{_DIR}/huo_dong.png"),
            "bu_gua": _bu_gua_wait,
            "bu_gua2": _bu_gua_click,
            "space_close": step_space_close,
            "gua_xiang": lambda ctx: do_click(ctx, f"{_DIR}/gua_xiang.png"),
            "scroll": lambda ctx: scroll_center(ctx, -120, times=5),
            "yue_ling": lambda ctx: do_click(ctx, f"{_DIR}/yue_ling.png"),
            "ling_qv": lambda ctx: do_click(ctx, f"{_DIR}/ling_qv.png"),
            "go_back": _finish,
        },
    )
