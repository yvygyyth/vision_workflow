"""战役商店流程动作。"""

from vision_workflow.events import click, scroll
from vision_workflow.module import EventFn

_DIR = "data/ming_jiang_sha/zhan_yi_store"
_COMMON = "data/ming_jiang_sha/common"

click_entry: EventFn = click().image(f"{_DIR}/entry.png", f"{_DIR}/entry2.png").execute()
click_zhan_yi_store: EventFn = click().image(f"{_DIR}/zhan_yi-store.png").execute()
click_ming_jiang_ce: EventFn = click().image(f"{_COMMON}/ming_jiang_ce.png").execute()
click_max: EventFn = click().image(f"{_COMMON}/max.png").execute()
click_buy: EventFn = click().image(f"{_DIR}/buy.png").execute()
click_space_close: EventFn = click().image(f"{_DIR}/space-close.png").execute()
scroll_store_list: EventFn = scroll().at("center").amount(-8).execute()
click_ling_xi_box: EventFn = click().image(f"{_COMMON}/ling_xi-box.png").execute()
click_buy2: EventFn = click().image(f"{_DIR}/buy2.png").execute()
click_close: EventFn = click().image(f"{_COMMON}/store-close.png").execute()
click_return_btn: EventFn = click().image(f"{_DIR}/return-btn.png").execute()
