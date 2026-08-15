"""链式事件 API。

用法::

    from vision_workflow.events import move, click, scroll, do

    do(move().image("a.png"), click())           # 识图移动再点击
    do(move().to(100, 200), click())             # 绝对移动再点击
    do(move().image("a.png"), move().by(0, 100), click())  # 识图后相对偏移再点
    do(move().at("center"), scroll(-200))        # 移到中心再滚轮
    move().by(10, 0).execute()                   # 只相对移动
"""

from vision_workflow.events.builders.click import click
from vision_workflow.events.builders.compose import do
from vision_workflow.events.builders.move import move
from vision_workflow.events.builders.scroll import scroll

__all__ = [
    "move",
    "click",
    "scroll",
    "do",
]
