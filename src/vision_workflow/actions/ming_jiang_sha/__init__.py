"""名将杀二级封装：Esc 语义 + common 模板点击。

与 ``events.builders`` 的通用链区分::

    from vision_workflow.events import click, scroll
    from vision_workflow.actions.ming_jiang_sha import space_close, go_back, buy, click_max
"""

from vision_workflow.actions.ming_jiang_sha.clicks import (
    buy,
    click_buy,
    click_ling_xi_box,
    click_max,
    click_ming_jiang_ce,
)
from vision_workflow.actions.ming_jiang_sha.go_back import go_back
from vision_workflow.actions.ming_jiang_sha.space_close import space_close

__all__ = [
    "buy",
    "click_buy",
    "click_max",
    "click_ming_jiang_ce",
    "click_ling_xi_box",
    "go_back",
    "space_close",
]
