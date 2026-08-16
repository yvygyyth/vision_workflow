"""输入文字事件：在当前焦点处键入字符串。"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Literal

from vision_workflow.input import input_text as do_input_text
from vision_workflow.module import EventFn, ModuleContext
from vision_workflow.status import FULFILLED, OutcomeKey

_Method = Literal["auto", "write", "paste"]


@dataclass(frozen=True)
class _InputText:
    text: str = ""
    key_interval: float = 0.0
    method: _Method = "auto"
    sleep: float = 0.2

    def content(self, text: str) -> _InputText:
        return replace(self, text=text)

    def interval(self, seconds: float) -> _InputText:
        """逐键间隔（仅 write 模式有效）。"""
        return replace(self, key_interval=max(0.0, seconds))

    def write(self) -> _InputText:
        """强制逐键输入。"""
        return replace(self, method="write")

    def paste(self) -> _InputText:
        """强制剪贴板粘贴。"""
        return replace(self, method="paste")

    def pause(self, seconds: float) -> _InputText:
        """输入后等待。"""
        return replace(self, sleep=seconds)

    def execute(self) -> EventFn:
        text = self.text
        key_interval = self.key_interval
        method = self.method
        sleep = self.sleep

        def _event(m: ModuleContext) -> OutcomeKey:
            m.log("input_text len=%s method=%s", len(text), method)
            do_input_text(text, interval=key_interval, method=method)
            if sleep > 0:
                m.sleep(sleep)
            return FULFILLED

        return _event


def input_text(text: str = "", *, interval: float = 0.0) -> _InputText:
    """输入字符串。可 ``input_text("hi")`` 或 ``input_text().content("hi")``。"""
    return _InputText(text=text, key_interval=interval)
