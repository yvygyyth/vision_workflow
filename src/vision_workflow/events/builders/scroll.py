"""滚轮事件：只在当前位置滚轮，不移动、不识图。"""

from __future__ import annotations

from dataclasses import dataclass, replace

from vision_workflow.module import EventFn, ModuleContext
from vision_workflow.status import FULFILLED, OutcomeKey


@dataclass(frozen=True)
class _Scroll:
    amount: int | None = None
    sleep: float = 0.3

    def by(self, amount: int) -> _Scroll:
        """滚轮刻度：>0 向上，<0 向下。"""
        return replace(self, amount=amount)

    def pause(self, seconds: float) -> _Scroll:
        return replace(self, sleep=seconds)

    def execute(self) -> EventFn:
        if self.amount is None:
            raise ValueError("scroll 需要 .by(n)")
        amount = self.amount
        sleep = self.sleep

        def _event(m: ModuleContext) -> OutcomeKey:
            m.log("滚轮 amount=%s", amount)
            chain = m.mouse().scroll(amount)
            if sleep > 0:
                chain = chain.sleep(sleep)
            chain.perform()
            return FULFILLED

        return _event


def scroll(amount: int | None = None) -> _Scroll:
    """当前位置滚轮。可 ``scroll(-200)`` 或 ``scroll().by(-200)``。"""
    return _Scroll(amount=amount)
