"""店铺流程动作。"""

from vision_workflow.events import click
from vision_workflow.module import EventFn

_DIR = "data/ming_jiang_sha/gong_hui"
_COMMON = "data/ming_jiang_sha/common"

click_entry: EventFn = click().image(f"{_DIR}/gong-hui-ru-kou.png", f"{_DIR}/gong-hui-ru-kou-2.png").execute()
click_gong_hui_store: EventFn = click().image(f"{_DIR}/gong-hui-store.png").execute()
click_max: EventFn = click().image(f"{_COMMON}/max.png").execute()
click_ming_jiang_ce: EventFn = click().image(f"{_COMMON}/ming_jiang_ce.png").execute()
click_buy: EventFn = click().image(f"{_DIR}/buy.png").execute()
click_ling_xi_box: EventFn = click().image(f"{_COMMON}/ling_xi-box.png").execute()
click_close: EventFn = click().image(f"{_COMMON}/store-close.png").execute()
