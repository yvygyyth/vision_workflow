"""子流程：公会店铺。"""

from vision_workflow.apps.ming_jiang_sha.common.actions import (
    confirm,
    click_ling_xi_box,
    click_max,
    click_ming_jiang_ce,
    go_back,
    space_close,
)
from vision_workflow.apps.ming_jiang_sha.parts.gong_hui.actions import (
    click_entry,
    click_hao_you,
    focus_search_input,
    
)
from vision_workflow.module import Flow, Module, abort, onward
from vision_workflow.status import FULFILLED, REJECTED

_CLICK = {FULFILLED: onward, REJECTED: abort}
_OK = {FULFILLED: onward}

FLOW = Flow(
    id="song_hua_store",
    name="日常送花",
    description="日常送花",
    entry="entry",
    modules=[
        Module(id="entry", name="进入好友列表", description="点击好友入口", event=click_hao_you, on=_CLICK),
        Module(id="qing_mei_store", name="搜索栏", description="点击搜索栏", event=focus_search_input, on=_CLICK),
        Module(id="ming_jiang_ce", name="名将册", description="选中名将册商品", event=click_ming_jiang_ce, on=_CLICK),
        Module(id="max", name="数量最大", description="将购买数量拉满", event=click_max, on=_CLICK),
        Module(id="buy", name="购买名将册", description="确认购买名将册", event=confirm, on=_CLICK),
        Module(id="space_close", name="关闭弹窗", description="Esc 关闭购买结果弹窗", event=space_close(), on=_OK),
        Module(id="close", name="关闭店铺", description="Esc 关闭公会店铺", event=go_back(), on=_OK),
        Module(id="return-btn", name="返回", description="Esc 返回主界面", event=go_back(), on=_OK),
    ],
)
