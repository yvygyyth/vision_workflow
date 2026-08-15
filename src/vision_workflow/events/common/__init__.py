"""名将杀共用 UI 事件（模板在 data/ming_jiang_sha/common）。

与 ``events.builders`` 的通用链区分::

    from vision_workflow.events import click          # 通用：click().image(本流程图)...
    from vision_workflow.events.common import click_max, buy
"""

from vision_workflow.events.common.clicks import (
    buy,
    click_buy,
    click_ling_xi_box,
    click_max,
    click_ming_jiang_ce,
)

__all__ = [
    "buy",
    "click_buy",
    "click_max",
    "click_ming_jiang_ce",
    "click_ling_xi_box",
]
