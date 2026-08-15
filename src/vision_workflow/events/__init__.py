"""链式事件 API。

用法::

    from vision_workflow.events import click, scroll
    from vision_workflow.actions.ming_jiang_sha import space_close, go_back, buy, click_max

    click().image("a.png").offset(0, 100).execute()   # 本流程专属图
    scroll().at("center").amount(-8).execute()
    space_close()  # Esc 关弹窗
    go_back()      # Esc 返回上一步
    click_max      # common/max.png
    buy            # common/buy.png，点模板底边下方 10px

目录约定::

    events/
      builders/   # 通用能力：click / scroll
      support/    # 共享内部实现
    actions/
      ming_jiang_sha/  # 名将杀二级封装（Esc 语义 + common 模板）
"""

from vision_workflow.events.builders.click import click
from vision_workflow.events.builders.scroll import scroll

__all__ = [
    "click",
    "scroll",
]
