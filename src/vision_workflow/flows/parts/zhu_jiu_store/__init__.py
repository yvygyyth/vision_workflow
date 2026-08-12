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
from vision_workflow.module import END, MISS, OK, Flow, Module, abort, onward

_CLICK = {OK: onward, MISS: abort}

FLOW = Flow(
    id="zhu_jiu_store",
    name="煮酒店铺",
    entry="entry",
    modules=[
        Module(id="entry", event=click_entry, on=_CLICK),
        Module(id="qing_mei_store", event=click_qing_mei_store, on=_CLICK),
        Module(id="ming_jiang_ce", event=click_ming_jiang_ce, on=_CLICK),
        Module(id="buy", event=click_buy, on=_CLICK),
        Module(id="space_close", event=click_space_close, on=_CLICK),
        Module(id="ling_xi-box", event=click_ling_xi_box, on=_CLICK),
        Module(id="buy2", event=click_buy, on=_CLICK),
        Module(id="space_close2", event=click_space_close2, on=_CLICK),
        Module(id="close", event=click_close, on=_CLICK),
        Module(id="return-btn", event=click_return_btn, on=_CLICK),
    ],
    success=END,
)
