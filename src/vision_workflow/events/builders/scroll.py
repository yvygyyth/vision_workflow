"""滚轮事件：只在当前位置滚轮，不移动、不识图。"""

from __future__ import annotations

from dataclasses import dataclass, replace

from vision_workflow.module import EventFn, ModuleContext
from vision_workflow.status import FULFILLED, OutcomeKey


@dataclass(frozen=True)
class _Scroll:
    amount: int | None = None
    count: int = 1
    gap: float = 0.05
    sleep: float = 0.3

    def by(self, amount: int) -> _Scroll:
        """单次滚轮刻度（距离）：>0 向上，<0 向下。"""
        return replace(self, amount=amount)

    def times(self, count: int) -> _Scroll:
        """滚动次数（游戏常忽略单次过大 delta，用多次小滚代替）。"""
        if count < 1:
            raise ValueError("times 至少为 1")
        return replace(self, count=count)

    def interval(self, seconds: float) -> _Scroll:
        """两次滚动之间的间隔（秒）。"""
        return replace(self, gap=max(0.0, seconds))

    def pause(self, seconds: float) -> _Scroll:
        """全部滚完后的等待。"""
        return replace(self, sleep=seconds)

    def execute(self) -> EventFn:
        if self.amount is None:
            raise ValueError("scroll 需要 .by(n) 或 scroll(n)")
        if self.count < 1:
            raise ValueError("times 至少为 1")
        amount = self.amount
        count = self.count
        gap = self.gap
        sleep = self.sleep

        def _event(m: ModuleContext) -> OutcomeKey:
            m.log("滚轮 amount=%s times=%s", amount, count)
            chain = m.mouse()
            for i in range(count):
                chain = chain.scroll(amount)
                if i < count - 1 and gap > 0:
                    chain = chain.sleep(gap)
            if sleep > 0:
                chain = chain.sleep(sleep)
            chain.perform()
            return FULFILLED

        return _event


def scroll(amount: int | None = None, *, times: int = 1) -> _Scroll:
    """当前位置滚轮。

    - ``scroll(-120)`` / ``scroll().by(-120)``：单次滚动量
    - ``scroll(-120).times(8)`` / ``scroll(-120, times=8)``：重复次数
    """
    if times < 1:
        raise ValueError("times 至少为 1")
    return _Scroll(amount=amount, count=times)
