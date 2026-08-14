"""霸青商店流程动作。"""

from vision_workflow.events import click, scroll
from vision_workflow.module import EventFn

_DIR = "data/ming_jiang_sha/ba_qing_store"
_COMMON = "data/ming_jiang_sha/common"

click_entry_icon: EventFn = click().image(f"{_DIR}/entry-icon.png").execute()
click_gold_tab: EventFn = click().image(f"{_DIR}/gold-tab.png").execute()
click_free_bingli: EventFn = click().image(f"{_DIR}/free-bingli.png").execute()
click_0buy: EventFn = click().image(f"{_DIR}/0buy.png").execute()
click_copper_tab: EventFn = click().image(f"{_DIR}/copper-tab.png").execute()
click_lingxi_box: EventFn = click().image(f"{_DIR}/lingxi-box.png").execute()
click_max: EventFn = click().image(f"{_COMMON}/max.png").execute()
click_500buy: EventFn = click().image(f"{_DIR}/500buy.png").execute()
click_jinlan_tab: EventFn = click().image(f"{_DIR}/jinlan-tab.png").execute()
scroll_down: EventFn = scroll().at("center").amount(-200).execute()
click_ming_jiang_ce: EventFn = click().image(f"{_DIR}/ming_jiang_ce.png").execute()
click_200buy: EventFn = click().image(f"{_DIR}/200buy.png").execute()
