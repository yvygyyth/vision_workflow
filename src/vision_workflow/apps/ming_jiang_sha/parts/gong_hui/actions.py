"""公会店铺流程动作。"""

from vision_workflow.apps.ming_jiang_sha.common.paths import DATA_ROOT
from vision_workflow.events import click, do, move
from vision_workflow.module import EventFn

_DIR = f"{DATA_ROOT}/gong_hui"

click_entry: EventFn = do(
    move().image(f"{_DIR}/gong-hui-ru-kou.png", f"{_DIR}/gong-hui-ru-kou-2.png"),
    click(),
)
click_gong_hui_store: EventFn = do(move().image(f"{_DIR}/gong-hui-store.png"), click())
click_wen_ding_ling: EventFn = do(move().image(f"{_DIR}/wen_ding_ling.png"), click())
click_tian_ming_ling: EventFn = do(move().image(f"{_DIR}/tian_ming_ling.png"), click())
click_tian_fa_ling: EventFn = do(move().image(f"{_DIR}/tian_fa_ling.png"), click())
click_jun_ling_zhuang: EventFn = do(move().image(f"{_DIR}/jun_ling_zhuang.png"), click())
