"""子流程：丹青阁。"""

from vision_workflow.apps.ming_jiang_sha.common.actions import go_back, space_close
from vision_workflow.apps.ming_jiang_sha.parts.dang_qing_ge.actions import (
    click_day_libao,
    click_icon,
)
from vision_workflow.module import Flow, Module, abort, onward
from vision_workflow.status import FULFILLED, REJECTED

_CLICK = {FULFILLED: onward, REJECTED: abort}
_OK = {FULFILLED: onward}

FLOW = Flow(
    id="dang_qing_ge",
    name="丹青阁",
    description="领取丹青阁每日礼包",
    entry="icon",
    modules=[
        Module(id="icon", name="打开丹青阁", description="点击丹青阁入口图标", event=click_icon, on=_CLICK),
        Module(id="day_libao", name="每日礼包", description="点击领取每日礼包", event=click_day_libao, on=_CLICK),
        Module(id="space_close", name="关闭弹窗", description="Esc 关闭领取结果弹窗", event=space_close(), on=_OK),
        Module(id="close", name="返回", description="Esc 返回主界面", event=go_back(), on=_OK),
    ],
)
