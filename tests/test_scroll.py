"""scroll builder：单次滚动量 + 次数。"""

from unittest.mock import MagicMock, call

from vision_workflow.events.builders.scroll import scroll
from vision_workflow.status import FULFILLED


def _ctx() -> MagicMock:
    m = MagicMock()
    chain = MagicMock()
    m.mouse.return_value = chain
    chain.scroll.return_value = chain
    chain.sleep.return_value = chain
    return m


def test_scroll_default_times_once() -> None:
    m = _ctx()
    key = scroll(-120).pause(0).interval(0).execute()(m)
    assert key == FULFILLED
    m.mouse.return_value.scroll.assert_called_once_with(-120)


def test_scroll_times_repeats_amount() -> None:
    m = _ctx()
    key = scroll(-3).times(4).pause(0).interval(0).execute()(m)
    assert key == FULFILLED
    assert m.mouse.return_value.scroll.call_args_list == [
        call(-3),
        call(-3),
        call(-3),
        call(-3),
    ]


def test_scroll_interval_between_repeats() -> None:
    m = _ctx()
    chain = m.mouse.return_value
    scroll(-5).times(3).interval(0.05).pause(0).execute()(m)
    # scroll, sleep, scroll, sleep, scroll — 无末尾 pause
    assert chain.scroll.call_count == 3
    assert chain.sleep.call_args_list == [call(0.05), call(0.05)]
