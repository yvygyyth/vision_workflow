"""scroll builder：单次滚动量 + 次数。"""

from unittest.mock import MagicMock, call, patch

from vision_workflow.events.builders.scroll import scroll
from vision_workflow.status import FULFILLED


def test_scroll_default_times_once() -> None:
    m = MagicMock()
    chain = MagicMock()
    chain.scroll.return_value = chain
    chain.sleep.return_value = chain
    with patch("vision_workflow.events.builders.scroll.Mouse", return_value=chain):
        key = scroll(-120).pause(0).interval(0).execute()(m)
    assert key == FULFILLED
    chain.scroll.assert_called_once_with(-120)


def test_scroll_times_repeats_amount() -> None:
    m = MagicMock()
    chain = MagicMock()
    chain.scroll.return_value = chain
    chain.sleep.return_value = chain
    with patch("vision_workflow.events.builders.scroll.Mouse", return_value=chain):
        key = scroll(-3).times(4).pause(0).interval(0).execute()(m)
    assert key == FULFILLED
    assert chain.scroll.call_args_list == [
        call(-3),
        call(-3),
        call(-3),
        call(-3),
    ]


def test_scroll_interval_between_repeats() -> None:
    m = MagicMock()
    chain = MagicMock()
    chain.scroll.return_value = chain
    chain.sleep.return_value = chain
    with patch("vision_workflow.events.builders.scroll.Mouse", return_value=chain):
        scroll(-5).times(3).interval(0.05).pause(0).execute()(m)
    assert chain.scroll.call_count == 3
    assert chain.sleep.call_args_list == [call(0.05), call(0.05)]
