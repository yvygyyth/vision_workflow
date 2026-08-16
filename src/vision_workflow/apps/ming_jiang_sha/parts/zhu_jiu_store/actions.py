"""煮酒店铺流程动作。"""

from vision_workflow.apps.ming_jiang_sha.common.paths import DATA_ROOT
from vision_workflow.events import click, do, move
from vision_workflow.module import EventFn

_DIR = f"{DATA_ROOT}/zhu_jiu_store"

click_entry: EventFn = do(move().image(f"{_DIR}/entry.png"), click())
click_qing_mei_store: EventFn = do(move().image(f"{_DIR}/qing_mei-store.png"), click())
