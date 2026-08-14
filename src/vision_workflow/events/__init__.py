"""链式事件 API。

用法::

    from vision_workflow.events import click, scroll

    click().image("a.png").offset(0, 100).execute()
    scroll().at("center").amount(-8).execute()

目录约定::

    events/
      builders/   # 每种事件一个文件（对外能力）
      support/    # 共享内部实现（识图、锚点等）
"""

from vision_workflow.events.builders.click import Click, click
from vision_workflow.events.builders.scroll import Scroll, scroll

__all__ = [
    "Click",
    "Scroll",
    "click",
    "scroll",
]
