"""执行单元。"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from vision_bot.runtime.context import RunContext
from vision_bot.runtime.result import Result

ActiveFn = Callable[[RunContext], Result]


@dataclass
class Module:
    id: str
    name: str
    active: ActiveFn
