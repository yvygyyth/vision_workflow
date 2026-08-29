"""滚轮动作（在当前位置滚动，需先 move）。"""

from __future__ import annotations

from dataclasses import dataclass, replace

from vision_bot.actions.context import ActionContext
from vision_bot.actions.fn import ActionFn
from vision_bot.core.input import Mouse
from vision_bot.runtime.result import Result


@dataclass(frozen=True)
class Scroll:
    amount: int = -120
    repeats: int = 1
    sleep: float = 0.05

    def times(self, repeats: int) -> Scroll:
        return replace(self, repeats=repeats)

    def pause(self, seconds: float) -> Scroll:
        return replace(self, sleep=seconds)

    def execute(self) -> ActionFn:
        amount = self.amount
        repeats = self.repeats
        sleep = self.sleep

        def _run(_ctx: ActionContext) -> Result:
            chain = Mouse()
            for i in range(repeats):
                chain = chain.scroll(amount)
                if sleep > 0 and i < repeats - 1:
                    chain = chain.sleep(sleep)
            chain.perform()
            return Result.success()

        return _run


def scroll(amount: int = -120) -> Scroll:
    return Scroll(amount=amount)
