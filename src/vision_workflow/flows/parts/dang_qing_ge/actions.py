"""丹青阁流程的专属事件。"""

from __future__ import annotations

from vision_workflow.events import click
from vision_workflow.module import EventFn

# 模板图：data/ming_jiang_sha/dang_qing_ge/
click_icon: EventFn = click("data/ming_jiang_sha/dang_qing_ge/dang_qing_ge-icon.png")
click_day_libao: EventFn = click("data/ming_jiang_sha/dang_qing_ge/day-libao.png")
# 识别 space-close，点击中心下方 100px
click_space_close: EventFn = click(
    "data/ming_jiang_sha/dang_qing_ge/space-close.png",
    offset_y=100,
)
click_close: EventFn = click("data/ming_jiang_sha/dang_qing_ge/close.png")
