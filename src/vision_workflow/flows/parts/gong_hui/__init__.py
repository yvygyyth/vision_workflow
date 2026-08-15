"""子流程：公会店铺。"""

from vision_workflow.events import go_back, space_close
from vision_workflow.events.common import buy, click_ling_xi_box, click_max, click_ming_jiang_ce
from vision_workflow.flows.parts.gong_hui.actions import (
    click_entry,
    click_gong_hui_store,
)
from vision_workflow.module import Flow, Module, abort, onward
from vision_workflow.status import FULFILLED, REJECTED

_CLICK = {FULFILLED: onward, REJECTED: abort}
_OK = {FULFILLED: onward}

FLOW = Flow(
    id="gong_hui_store",
    name="公会店铺",
    description="在公会铺购买名将册与灵犀宝匣",
    entry="entry",
    modules=[
        Module(id="entry", name="进入公会", description="点击公会入口", event=click_entry, on=_CLICK),
        Module(id="qing_mei_store", name="公会店铺", description="进入公会店铺", event=click_gong_hui_store, on=_CLICK),
        Module(id="ming_jiang_ce", name="名将册", description="选中名将册商品", event=click_ming_jiang_ce, on=_CLICK),
        Module(id="max", name="数量最大", description="将购买数量拉满", event=click_max, on=_CLICK),
        Module(id="buy", name="购买名将册", description="确认购买名将册", event=buy, on=_CLICK),
        Module(id="space_close", name="关闭弹窗", description="Esc 关闭购买结果弹窗", event=space_close(), on=_OK),
        Module(id="ling_xi-box", name="灵犀宝匣", description="选中灵犀宝匣商品", event=click_ling_xi_box, on=_CLICK),
        Module(id="buy2", name="购买灵犀宝匣", description="确认购买灵犀宝匣", event=buy, on=_CLICK),
        Module(id="space_close2", name="关闭弹窗", description="Esc 再次关闭购买结果弹窗", event=space_close(), on=_OK),
        Module(id="close", name="关闭店铺", description="Esc 关闭公会店铺", event=go_back(), on=_OK),
        Module(id="return-btn", name="返回", description="Esc 返回主界面", event=go_back(), on=_OK),
    ],
)
