"""子流程：战役商店。"""

from vision_workflow.flows.parts.zhan_yi_store.actions import (
    click_buy,
    click_buy2,
    click_close,
    click_entry,
    click_ling_xi_box,
    click_max,
    click_ming_jiang_ce,
    click_return_btn,
    click_space_close,
    click_zhan_yi_store,
    scroll_store_list,
)
from vision_workflow.module import Flow, Module, abort, onward
from vision_workflow.status import FULFILLED, REJECTED

_CLICK = {FULFILLED: onward, REJECTED: abort}
_FULFILLED = {FULFILLED: onward}

FLOW = Flow(
    id="zhan_yi_store",
    name="战役商店",
    description="在战役商店购买名将册与灵犀宝匣",
    entry="entry",
    modules=[
        Module(id="entry", name="进入战役", description="点击战役入口", event=click_entry, on=_CLICK),
        Module(id="zhan_yi_store", name="打开商店", description="进入战役商店", event=click_zhan_yi_store, on=_CLICK),
        Module(id="ming_jiang_ce", name="名将册", description="选中名将册商品", event=click_ming_jiang_ce, on=_CLICK),
        Module(id="max", name="数量最大", description="将购买数量拉满", event=click_max, on=_CLICK),
        Module(id="buy", name="购买名将册", description="确认购买名将册", event=click_buy, on=_CLICK),
        Module(id="space_close", name="空白关闭弹窗", description="关闭购买结果弹窗", event=click_space_close, on=_CLICK),
        Module(id="scroll", name="滑动商品列表", description="下滑商店列表以露出灵犀宝匣", event=scroll_store_list, on=_FULFILLED),
        Module(id="ling_xi-box", name="灵犀宝匣", description="选中灵犀宝匣商品", event=click_ling_xi_box, on=_CLICK),
        Module(id="max2", name="数量最大", description="将购买数量拉满", event=click_max, on=_CLICK),
        Module(id="buy2", name="购买灵犀宝匣", description="确认购买灵犀宝匣", event=click_buy2, on=_CLICK),
        Module(id="space_close2", name="空白关闭弹窗", description="再次关闭购买结果弹窗", event=click_space_close, on=_CLICK),
        Module(id="close", name="关闭商店", description="关闭战役商店", event=click_close, on=_CLICK),
        Module(id="return-btn", name="返回", description="返回主界面", event=click_return_btn, on=_CLICK),
    ],
)
