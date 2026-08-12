"""丹青阁流程的专属事件。"""

from __future__ import annotations

from vision_workflow.events import click_image
from vision_workflow.module import EventFn

_DIR = "data/ming_jiang_sha/dang_qing_ge"

click_icon: EventFn = click_image(f"{_DIR}/dang_qing_ge-icon.png")
click_day_libao: EventFn = click_image(f"{_DIR}/day-libao.png")
# 识别 space-close，点击中心下方 100px
click_space_close: EventFn = click_image(f"{_DIR}/space-close.png", offset_y=100)
click_close: EventFn = click_image(f"{_DIR}/close.png")
