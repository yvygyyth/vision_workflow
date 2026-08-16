"""子流程：千里单骑。"""

from vision_workflow.apps.ming_jiang_sha.parts.qian_li_dan_qi.actions import (
    click_search_input,
    click_select_wu_jiang,
    type_wu_jiang,
)
from vision_workflow.module import Flow, Module, abort, onward
from vision_workflow.status import FULFILLED, REJECTED

_CLICK = {FULFILLED: onward, REJECTED: abort}
_OK = {FULFILLED: onward}

FLOW = Flow(
    id="qian_li_dan_qi",
    name="千里单骑",
    description="选择武将并搜索输入武将名",
    entry="select_wu_jiang",
    params={"wu_jiang": "吕布"},
    modules=[
        Module(
            id="select_wu_jiang",
            name="选择武将",
            description="点击选择武将入口",
            event=click_select_wu_jiang,
            on=_CLICK,
        ),
        Module(
            id="search_input",
            name="打开搜索框",
            description="识图 search 后向左偏移 50 像素点击",
            event=click_search_input,
            on=_CLICK,
        ),
        Module(
            id="type_wu_jiang",
            name="输入武将名",
            description="输入入参 wu_jiang（默认吕布）",
            event=type_wu_jiang,
            on=_OK,
        ),
    ],
)
