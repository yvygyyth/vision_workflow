"""煮酒店铺流程的专属事件。"""

from __future__ import annotations

from vision_workflow.events import click
from vision_workflow.module import EventFn

# 模板图：data/samples/zhu_jiu_store/
click_entry: EventFn = click("data/samples/zhu_jiu_store/entry.png")
click_qing_mei_store: EventFn = click("data/samples/zhu_jiu_store/qing_mei-store.png")
click_ming_jiang_ce: EventFn = click("data/samples/zhu_jiu_store/ming_jiang_ce.png")
click_buy1: EventFn = click("data/samples/zhu_jiu_store/buy1.png")
click_space_close: EventFn = click(
    "data/samples/zhu_jiu_store/space-close.png",
    offset_y=100,
)
