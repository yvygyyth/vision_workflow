"""活动流程动作。"""

from vision_workflow.apps.ming_jiang_sha.common.paths import DATA_ROOT
from vision_workflow.events import click, do, move, scroll
from vision_workflow.module import EventFn

_DIR = f"{DATA_ROOT}/actaivity"

click_huo_dong: EventFn = do(move().image(f"{_DIR}/huo_dong.png"), click())
click_gua_xiang: EventFn = do(move().image(f"{_DIR}/gua_xiang.png"), click())
click_yue_ling: EventFn = do(move().image(f"{_DIR}/yue_ling.png"), click())
click_ling_qv: EventFn = do(move().image(f"{_DIR}/ling_qv.png"), click())
scroll_down: EventFn = do(move().at("center"), scroll(-120).times(5))
click_ming_jiang_ce: EventFn = do(move().image(f"{_DIR}/ming_jiang_ce.png"), click())
move_aside: EventFn = do(move().to(1400, 600), click())