"""丹青阁。"""

from __future__ import annotations

from vision_bot.actions import click, do, move
from vision_bot.apps.ming_jiang_sha.actions import step_go_back, step_space_close
from vision_bot.apps.ming_jiang_sha.paths import DATA_ROOT
from vision_bot.runtime.builders import flow, mod
from vision_bot.runtime.flow import Flow
from vision_bot.runtime.result import Result

_DIR = f"{DATA_ROOT}/dang_qing_ge"


def _open_icon(ctx) -> Result:
    return do(move().image(f"{_DIR}/dang_qing_ge-icon.png"), click())(ctx.action_ctx())


def _day_libao(ctx) -> Result:
    return do(move().image(f"{_DIR}/day-libao.png"), click())(ctx.action_ctx())


def build() -> Flow:
    return flow(
        "fee_day.dang_qing_ge",
        "丹青阁",
        children=[
            mod("fee_day.dang_qing_ge.icon", "打开丹青阁", _open_icon),
            mod("fee_day.dang_qing_ge.day_libao", "每日礼包", _day_libao),
            mod("fee_day.dang_qing_ge.space_close", "关闭弹窗", step_space_close),
            mod("fee_day.dang_qing_ge.back", "返回", step_go_back),
        ],
    )
