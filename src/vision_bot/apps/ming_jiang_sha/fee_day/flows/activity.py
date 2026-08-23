"""活动领取。"""

from __future__ import annotations

from vision_bot.actions import click, do, move
from vision_bot.apps.ming_jiang_sha.actions import step_go_back, step_space_close
from vision_bot.apps.ming_jiang_sha.flow_helpers import do_click, scroll_center
from vision_bot.apps.ming_jiang_sha.paths import DATA_ROOT
from vision_bot.runtime.builders import flow, mod
from vision_bot.runtime.flow import Flow
from vision_bot.runtime.result import Result

_DIR = f"{DATA_ROOT}/actaivity"


def _bu_gua_wait(ctx) -> Result:
    ctx.sleep(3.0)
    do(move().to(1400, 600).raw(), click())(ctx.action_ctx())
    return Result.success()


def _bu_gua_click(ctx) -> Result:
    do(move().to(1400, 600).raw(), click())(ctx.action_ctx())
    return Result.success()


def _finish(ctx) -> Result:
    step_go_back(ctx)
    return Result.success()


def build() -> Flow:
    return flow(
        "fee_day.activity",
        "活动",
        children=[
            mod("fee_day.activity.entry", "打开活动", lambda ctx: do_click(ctx, f"{_DIR}/huo_dong.png")),
            mod("fee_day.activity.bu_gua", "卜卦等待", _bu_gua_wait),
            mod("fee_day.activity.bu_gua2", "卜卦点击", _bu_gua_click),
            mod("fee_day.activity.space_close", "关闭弹窗", step_space_close),
            mod("fee_day.activity.gua_xiang", "卦象", lambda ctx: do_click(ctx, f"{_DIR}/gua_xiang.png")),
            mod("fee_day.activity.scroll", "滚动", lambda ctx: scroll_center(ctx, -120, times=5)),
            mod("fee_day.activity.yue_ling", "月灵", lambda ctx: do_click(ctx, f"{_DIR}/yue_ling.png")),
            mod("fee_day.activity.ling_qv", "领取", lambda ctx: do_click(ctx, f"{_DIR}/ling_qv.png")),
            mod("fee_day.activity.go_back", "返回", _finish),
        ],
    )
