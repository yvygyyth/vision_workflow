"""动作函数类型。"""

from __future__ import annotations

from collections.abc import Callable

from vision_bot.actions.context import ActionContext
from vision_bot.runtime.result import Result

ActionFn = Callable[[ActionContext], Result]
