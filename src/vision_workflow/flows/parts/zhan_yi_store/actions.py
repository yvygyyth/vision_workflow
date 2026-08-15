"""战役商店流程动作。"""

from vision_workflow.events import click, scroll
from vision_workflow.module import EventFn

_DIR = "data/ming_jiang_sha/zhan_yi_store"

click_entry: EventFn = click().image(f"{_DIR}/entry.png", f"{_DIR}/entry2.png").execute()
click_zhan_yi_store: EventFn = click().image(f"{_DIR}/zhan_yi-store.png").execute()
click_buy: EventFn = click().image(f"{_DIR}/buy.png").execute()
scroll_store_list: EventFn = scroll().at("center").amount(-200).execute()
click_buy2: EventFn = click().image(f"{_DIR}/buy2.png").execute()
