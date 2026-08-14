"""丹青阁流程动作。"""

from vision_workflow.events import click
from vision_workflow.module import EventFn

_DIR = "data/ming_jiang_sha/dang_qing_ge"

click_icon: EventFn = click().image(f"{_DIR}/dang_qing_ge-icon.png").execute()
click_day_libao: EventFn = click().image(f"{_DIR}/day-libao.png").execute()
click_space_close: EventFn = click().image(f"{_DIR}/space-close.png").offset(0, 100).execute()
click_close: EventFn = click().image(f"{_DIR}/close.png").execute()
