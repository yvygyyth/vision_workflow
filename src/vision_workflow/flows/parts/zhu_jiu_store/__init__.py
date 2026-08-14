"""子流程：煮酒店铺。"""

from vision_workflow.flows.parts.zhu_jiu_store.actions import (
    click_buy,
    click_entry,
    click_ming_jiang_ce,
    click_qing_mei_store,
    click_space_close,
    click_ling_xi_box,
    click_space_close2,
    click_close,
    click_return_btn,
)
from vision_workflow.module import Flow, Module, abort, onward
from vision_workflow.status import FULFILLED, REJECTED

_CLICK = {FULFILLED: onward, REJECTED: abort}

FLOW = Flow(
    id="zhu_jiu_store",
    name="煮酒店铺",
    description="在煮酒/青梅铺购买名将册与灵犀宝匣",
    entry="entry",
    modules=[
        Module(id="entry", name="进入煮酒", description="点击煮酒入口", event=click_entry, on=_CLICK),
        Module(id="qing_mei_store", name="青梅店铺", description="进入青梅店铺", event=click_qing_mei_store, on=_CLICK),
        Module(id="ming_jiang_ce", name="名将册", description="选中名将册商品", event=click_ming_jiang_ce, on=_CLICK),
        Module(id="buy", name="购买名将册", description="确认购买名将册", event=click_buy, on=_CLICK),
        Module(id="space_close", name="空白关闭弹窗", description="关闭购买结果弹窗", event=click_space_close, on=_CLICK),
        Module(id="ling_xi-box", name="灵犀宝匣", description="选中灵犀宝匣商品", event=click_ling_xi_box, on=_CLICK),
        Module(id="buy2", name="购买灵犀宝匣", description="确认购买灵犀宝匣", event=click_buy, on=_CLICK),
        Module(id="space_close2", name="空白关闭弹窗", description="再次关闭购买结果弹窗", event=click_space_close2, on=_CLICK),
        Module(id="close", name="关闭店铺", description="关闭青梅店铺", event=click_close, on=_CLICK),
        Module(id="return-btn", name="返回", description="返回主界面", event=click_return_btn, on=_CLICK),
    ],
)
