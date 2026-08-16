"""点击事件：只在当前位置点击，不移动、不识图。"""

from __future__ import annotations

from dataclasses import dataclass, replace

from vision_workflow.input import Button
from vision_workflow.module import EventFn, ModuleContext
from vision_workflow.status import FULFILLED, OutcomeKey


@dataclass(frozen=True)
class _Click:
    button: Button = "left"
    clicks: int = 1
    sleep: float = 0.2

    def button_as(self, button: Button) -> _Click:
        return replace(self, button=button)

    def times(self, clicks: int) -> _Click:
        return replace(self, clicks=clicks)

    def pause(self, seconds: float) -> _Click:
        return replace(self, sleep=seconds)

    def execute(self) -> EventFn:
        button = self.button
        clicks = self.clicks
        sleep = self.sleep

        def _event(m: ModuleContext) -> OutcomeKey:
            chain = m.mouse().click(button=button, clicks=clicks)
            if sleep > 0:
                chain = chain.sleep(sleep)
            chain.perform()
            return FULFILLED

        return _event


def click(*, button: Button = "left", clicks: int = 1) -> _Click:
    """当前位置点击。"""
    return _Click(button=button, clicks=clicks)
