"""点击动作。"""

from __future__ import annotations

from dataclasses import dataclass, replace

from vision_bot.actions.context import ActionContext
from vision_bot.actions.fn import ActionFn
from vision_bot.core.input import DEFAULT_CLICK_HOLD_SEC, Button, Mouse
from vision_bot.runtime.result import Result


@dataclass(frozen=True)
class Click:
    button: Button = "left"
    clicks: int = 1
    sleep: float = 0.2
    hold: float = DEFAULT_CLICK_HOLD_SEC

    def button_as(self, button: Button) -> Click:
        return replace(self, button=button)

    def times(self, clicks: int) -> Click:
        return replace(self, clicks=clicks)

    def pause(self, seconds: float) -> Click:
        return replace(self, sleep=seconds)

    def hold_for(self, seconds: float) -> Click:
        return replace(self, hold=seconds)

    def execute(self) -> ActionFn:
        button = self.button
        clicks = self.clicks
        sleep = self.sleep
        hold = self.hold

        def _run(_ctx: ActionContext) -> Result:
            chain = Mouse().click(button=button, clicks=clicks, hold=hold)
            if sleep > 0:
                chain = chain.sleep(sleep)
            chain.perform()
            return Result.success()

        return _run


def click(*, button: Button = "left", clicks: int = 1) -> Click:
    return Click(button=button, clicks=clicks)
