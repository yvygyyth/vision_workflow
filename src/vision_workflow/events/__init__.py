"""链式事件 API。

用法::

    from vision_workflow.events import click, scroll, space_close, go_back
    from vision_workflow.events.common import click_max  # 共用模板，勿与上方通用链混用

    click().image("a.png").offset(0, 100).execute()   # 本流程专属图
    scroll().at("center").amount(-8).execute()
    space_close()  # Esc 关弹窗
    go_back()      # Esc 返回上一步
    click_max      # common/max.png

目录约定::

    events/
      builders/   # 通用能力：click / scroll / Esc…
      common/     # 名将杀共用图点击（data/.../common）
      support/    # 共享内部实现
"""

from vision_workflow.events.builders.click import click
from vision_workflow.events.builders.go_back import go_back
from vision_workflow.events.builders.scroll import scroll
from vision_workflow.events.builders.space_close import space_close

__all__ = [
    "click",
    "scroll",
    "space_close",
    "go_back",
]
