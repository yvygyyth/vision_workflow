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
from vision_workflow.module import END, MISS, OK, Flow, Module, abort, onward

_CLICK = {OK: onward, MISS: abort}
_OK = {OK: onward}

FLOW = Flow(
    id="zhan_yi_store",
    name="战役商店",
    entry="entry",
    modules=[
        Module(id="entry", event=click_entry, on=_CLICK),
        Module(id="zhan_yi_store", event=click_zhan_yi_store, on=_CLICK),
        Module(id="ming_jiang_ce", event=click_ming_jiang_ce, on=_CLICK),
        Module(id="max", event=click_max, on=_CLICK),
        Module(id="buy", event=click_buy, on=_CLICK),
        Module(id="space_close", event=click_space_close, on=_CLICK),
        Module(id="scroll", event=scroll_store_list, on=_OK),
        Module(id="ling_xi-box", event=click_ling_xi_box, on=_CLICK),
        Module(id="max2", event=click_max, on=_CLICK),
        Module(id="buy2", event=click_buy2, on=_CLICK),
        Module(id="space_close2", event=click_space_close, on=_CLICK),
        Module(id="close", event=click_close, on=_CLICK),
        Module(id="return-btn", event=click_return_btn, on=_CLICK),
    ],
    success=END,
)
