"""input_text 事件：输入字符串。"""

from unittest.mock import MagicMock, patch

from vision_workflow.events.builders.input_text import input_text
from vision_workflow.status import FULFILLED


def test_input_text_ascii_uses_write() -> None:
    m = MagicMock()
    with patch("vision_workflow.events.builders.input_text.do_input_text") as typed:
        key = input_text("hello").pause(0).execute()(m)
    assert key == FULFILLED
    typed.assert_called_once_with("hello", interval=0.0, method="auto")


def test_input_text_interval_and_paste() -> None:
    m = MagicMock()
    with patch("vision_workflow.events.builders.input_text.do_input_text") as typed:
        input_text("张飞").interval(0.05).paste().pause(0).execute()(m)
    typed.assert_called_once_with("张飞", interval=0.05, method="paste")
