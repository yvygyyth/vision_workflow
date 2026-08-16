"""链式事件 API。

用法::

    from vision_workflow.events import move, click, scroll, do

    do(move().image("a.png"), click())           # 识图移动再点击
    do(move().to(100, 200), click())             # 绝对移动（默认按分辨率缩放）
    do(move().to(100, 200).raw(), click())       # 绝对像素，不缩放
    do(move().image("a.png"), move().by(0, 100), click())  # 识图后相对偏移再点
    do(move().at("center"), scroll(-120).times(8))  # 移到中心再滚轮（多次小滚）
    move().by(10, 0).execute()                   # 只相对移动（默认缩放）
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
