"""煮酒店铺流程动作。"""

from vision_workflow.events import click
from vision_workflow.module import EventFn

_DIR = "data/ming_jiang_sha/zhu_jiu_store"
_COMMON = "data/ming_jiang_sha/common"

click_entry: EventFn = click().image(f"{_DIR}/entry.png").execute()
click_qing_mei_store: EventFn = click().image(f"{_DIR}/qing_mei-store.png").execute()
click_ming_jiang_ce: EventFn = click().image(f"{_COMMON}/ming_jiang_ce.png").execute()
click_buy: EventFn = click().image(f"{_DIR}/buy.png").execute()
click_ling_xi_box: EventFn = click().image(f"{_COMMON}/ling_xi-box.png").execute()
