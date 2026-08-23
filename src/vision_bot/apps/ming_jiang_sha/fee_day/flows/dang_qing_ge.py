"""丹青阁。"""

from __future__ import annotations

from vision_bot.apps.ming_jiang_sha.actions import step_go_back, step_space_close
from vision_bot.apps.ming_jiang_sha.flow_helpers import do_click
from vision_bot.apps.ming_jiang_sha.paths import DATA_ROOT
from vision_bot.runtime.flow import Flow, StepResult

_DIR = f"{DATA_ROOT}/dang_qing_ge"
DONE = "dang_done"


def _finish(ctx) -> StepResult:
    step_go_back(ctx)
    return StepResult.end(DONE)


def build() -> Flow:
    return Flow(
        id="dang_qing_ge",
        name="丹青阁",
        entry="icon",
        steps={
            "icon": lambda ctx: do_click(ctx, f"{_DIR}/dang_qing_ge-icon.png"),
            "day_libao": lambda ctx: do_click(ctx, f"{_DIR}/day-libao.png"),
            "space_close": step_space_close,
            "go_back": _finish,
        },
    )
