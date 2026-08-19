"""活动流程动作。"""

from vision_workflow.apps.ming_jiang_sha.common.paths import DATA_ROOT
from vision_workflow.events import click, do, move, scroll
from vision_workflow.module import EventFn

_DIR = f"{DATA_ROOT}/ba_qing_store"

click_huo_dong: EventFn = do(move().image(f"{_DIR}/huo_dong.png"), click())
click_gold_tab: EventFn = do(move().image(f"{_DIR}/gold-tab.png"), click())
click_free_bingli: EventFn = do(move().image(f"{_DIR}/free-bingli.png"), click())
click_copper_tab: EventFn = do(move().image(f"{_DIR}/copper-tab.png"), click())
click_lingxi_box: EventFn = do(move().image(f"{_DIR}/lingxi-box.png"), click())
click_jinlan_tab: EventFn = do(move().image(f"{_DIR}/jinlan-tab.png"), click())
scroll_down: EventFn = do(move().at("center"), scroll(-120).times(5))
click_ming_jiang_ce: EventFn = do(move().image(f"{_DIR}/ming_jiang_ce.png"), click())
move_aside: EventFn = do(move().to(1400, 600), click())