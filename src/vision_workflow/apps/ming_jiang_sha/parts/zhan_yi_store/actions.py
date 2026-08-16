"""战役商店流程动作。"""

from vision_workflow.apps.ming_jiang_sha.common.paths import DATA_ROOT
from vision_workflow.events import click, do, move, scroll
from vision_workflow.module import EventFn

_DIR = f"{DATA_ROOT}/zhan_yi_store"

click_entry: EventFn = do(
    move().image(f"{_DIR}/entry.png", f"{_DIR}/entry2.png"), click()
)
click_zhan_yi_store: EventFn = do(move().image(f"{_DIR}/zhan_yi-store.png"), click())
scroll_store_list: EventFn = do(move().at("center"), scroll(-120).times(10))
