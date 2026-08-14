"""链式事件 API。

用法::

    from vision_workflow.events import click, scroll, space_close

    click().image("a.png").offset(0, 100).execute()
    scroll().at("center").amount(-8).execute()
    space_close()  # Esc 关弹窗
"""

from vision_workflow.events.builders.click import click
from vision_workflow.events.builders.scroll import scroll
from vision_workflow.events.builders.space_close import space_close

__all__ = [
    "click",
    "scroll",
    "space_close",
]
