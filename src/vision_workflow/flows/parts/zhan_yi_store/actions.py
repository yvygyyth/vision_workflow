"""战役商店流程的专属事件。"""

from __future__ import annotations

from vision_workflow.events import click_image, scroll_at
from vision_workflow.module import EventFn

_DIR = "data/ming_jiang_sha/zhan_yi_store"
_COMMON = "data/ming_jiang_sha/common"

# entry / entry2 任一即可，优先 entry
click_entry: EventFn = click_image(f"{_DIR}/entry.png", f"{_DIR}/entry2.png")
click_zhan_yi_store: EventFn = click_image(f"{_DIR}/zhan_yi-store.png")
click_ming_jiang_ce: EventFn = click_image(f"{_COMMON}/ming_jiang_ce.png")
click_max: EventFn = click_image(f"{_COMMON}/max.png")
click_buy: EventFn = click_image(f"{_DIR}/buy.png")
click_space_close: EventFn = click_image(f"{_DIR}/space-close.png")
# 列表下滚，露出下方商品（灵犀宝匣等）；距离可按实机再调
scroll_store_list: EventFn = scroll_at("center", amount=-8)
click_ling_xi_box: EventFn = click_image(f"{_COMMON}/ling_xi-box.png")
click_buy2: EventFn = click_image(f"{_DIR}/buy2.png")
click_close: EventFn = click_image(f"{_COMMON}/store-close.png")
click_return_btn: EventFn = click_image(f"{_DIR}/return-btn.png")
