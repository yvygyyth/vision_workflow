"""千里单骑 · 开打动作。"""

from __future__ import annotations

from vision_workflow.apps.ming_jiang_sha.common.paths import DATA_ROOT
from vision_workflow.events import click, do, move
from vision_workflow.module import EventFn

_DIR = f"{DATA_ROOT}/qian_li_dan_qi/fight"

click_cancel: EventFn = do(move().image(f"{_DIR}/cancel.png"), click())
# 勿用 (0,0)：PyAutoGUI 角落 FailSafe 会导致后续操作抛异常
move_aside: EventFn = do(move().to(80, 80).raw())
click_setting: EventFn = do(move().image(f"{_DIR}/setting.png"), click())
click_auto: EventFn = do(move().image(f"{_DIR}/auto.png"), click())
click_challenge_end: EventFn = do(
    move().image(f"{_DIR}/challenge_end.png").match(timeout=600, interval=5),
    click(),
)
click_next_step: EventFn = do(move().image(f"{_DIR}/next_step.png"), click())
