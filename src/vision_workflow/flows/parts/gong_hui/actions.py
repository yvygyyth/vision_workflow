"""公会店铺流程动作。"""

from vision_workflow.events import click, do, move
from vision_workflow.module import EventFn

_DIR = "data/ming_jiang_sha/gong_hui"

click_entry: EventFn = do(
    move().image(f"{_DIR}/gong-hui-ru-kou.png", f"{_DIR}/gong-hui-ru-kou-2.png"),
    click(),
)
click_gong_hui_store: EventFn = do(move().image(f"{_DIR}/gong-hui-store.png"), click())
