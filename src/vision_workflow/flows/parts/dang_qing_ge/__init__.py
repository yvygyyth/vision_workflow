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
    description="领取丹青阁每日礼包",
    entry="icon",
    modules=[
        Module(
            id="icon",
            name="打开丹青阁",
            description="点击丹青阁入口图标",
            event=click_icon,
            on=_CLICK,
        ),
        Module(
            id="day_libao",
            name="每日礼包",
            description="点击领取每日礼包",
            event=click_day_libao,
            on=_CLICK,
        ),
        Module(
            id="space_close",
            name="空白关闭弹窗",
            description="点击空白处关闭领取结果弹窗",
            event=click_space_close,
            on=_CLICK,
        ),
        Module(
            id="close",
            name="关闭丹青阁",
            description="关闭界面返回主界面",
            event=click_close,
            on=_CLICK,
        ),
    ],
)
