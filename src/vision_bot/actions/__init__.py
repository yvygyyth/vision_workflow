"""链式动作 API。"""

from vision_bot.actions.click import click
from vision_bot.actions.compose import do
from vision_bot.actions.context import action_context
from vision_bot.actions.move import move
from vision_bot.actions.scroll import scroll

__all__ = ["move", "click", "scroll", "do", "action_context"]
