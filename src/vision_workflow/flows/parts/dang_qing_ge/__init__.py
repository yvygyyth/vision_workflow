"""子流程：丹青阁。"""

from vision_workflow.flows.parts.dang_qing_ge.actions import (
    click_close,
    click_day_libao,
    click_icon,
    click_space_close,
)
from vision_workflow.module import Flow, Module, abort, onward
from vision_workflow.status import FULFILLED, REJECTED

_CLICK = {FULFILLED: onward, REJECTED: abort}

FLOW = Flow(
    id="dang_qing_ge",
    name="丹青阁",
    entry="icon",
    modules=[
        Module(id="icon", event=click_icon, on=_CLICK),
        Module(id="day_libao", event=click_day_libao, on=_CLICK),
        Module(id="space_close", event=click_space_close, on=_CLICK),
        Module(id="close", event=click_close, on=_CLICK),
    ],
)
