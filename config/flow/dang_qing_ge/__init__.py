"""子流程：丹青阁。"""

from config.flow.dang_qing_ge.actions import (
    click_close,
    click_day_libao,
    click_icon,
    click_space_close,
)
from vision_workflow.module import END, Flow, Module

FLOW = Flow(
    id="dang_qing_ge",
    name="丹青阁",
    entry="icon",
    modules=[
        Module(id="icon", event=click_icon),
        Module(id="day_libao", event=click_day_libao),
        Module(id="space_close", event=click_space_close),
        Module(id="close", event=click_close),
    ],
    success=END,
)
