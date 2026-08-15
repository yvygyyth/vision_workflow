"""丹青阁流程动作。"""

from vision_workflow.events import click, do, move
from vision_workflow.module import EventFn

_DIR = "data/ming_jiang_sha/dang_qing_ge"

click_icon: EventFn = do(move().image(f"{_DIR}/dang_qing_ge-icon.png"), click())
click_day_libao: EventFn = do(move().image(f"{_DIR}/day-libao.png"), click())
