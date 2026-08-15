"""煮酒店铺流程动作。"""

from vision_workflow.events import click
from vision_workflow.module import EventFn

_DIR = "data/ming_jiang_sha/zhu_jiu_store"

click_entry: EventFn = click().image(f"{_DIR}/entry.png").execute()
click_qing_mei_store: EventFn = click().image(f"{_DIR}/qing_mei-store.png").execute()
