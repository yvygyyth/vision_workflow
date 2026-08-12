"""煮酒店铺流程的专属事件。"""

from __future__ import annotations

from vision_workflow.events import click
from vision_workflow.module import EventFn

# 模板图：data/ming_jiang_sha/zhu_jiu_store/
click_entry: EventFn = click("data/ming_jiang_sha/zhu_jiu_store/entry.png")
click_qing_mei_store: EventFn = click("data/ming_jiang_sha/zhu_jiu_store/qing_mei-store.png")
click_ming_jiang_ce: EventFn = click("data/ming_jiang_sha/common/ming_jiang_ce.png")
click_buy: EventFn = click("data/ming_jiang_sha/zhu_jiu_store/buy.png")
click_space_close: EventFn = click(
    "data/ming_jiang_sha/zhu_jiu_store/space-close.png"
)
click_ling_xi_box: EventFn = click("data/ming_jiang_sha/common/ling_xi-box.png")
click_space_close2: EventFn = click(
    "data/ming_jiang_sha/zhu_jiu_store/space-close2.png"
)
click_close: EventFn = click("data/ming_jiang_sha/common/store-close.png")
click_return_btn: EventFn = click("data/ming_jiang_sha/common/return-btn.png")