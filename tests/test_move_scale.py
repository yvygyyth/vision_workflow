"""move：绝对/相对坐标默认按显示基准缩放。"""

from unittest.mock import MagicMock, patch

from vision_workflow.events.builders.move import move
from vision_workflow.status import FULFILLED


def _ctx() -> MagicMock:
    m = MagicMock()
    chain = MagicMock()
    m.mouse.return_value = chain
    chain.move.return_value = chain
    chain.sleep.return_value = chain
    return m


def test_to_scales_by_default() -> None:
    m = _ctx()
    with patch(
        "vision_workflow.events.builders.move.cached_template_scale",
        return_value=2.0,
    ):
        key = move().to(100, 50).pause(0).execute()(m)
    assert key == FULFILLED
    m.mouse.return_value.move.assert_called_once_with(200, 100, duration=0.15)


def test_by_scales_by_default() -> None:
    m = _ctx()
    with patch(
        "vision_workflow.events.builders.move.cached_template_scale",
        return_value=1.5,
    ):
        move().by(10, -20).pause(0).execute()(m)
    m.mouse.return_value.move.assert_called_once_with(
        15, -30, relative=True, duration=0.15
    )


def test_raw_skips_scale() -> None:
    m = _ctx()
    with patch(
        "vision_workflow.events.builders.move.cached_template_scale",
        return_value=2.0,
    ):
        move().to(100, 50).raw().pause(0).execute()(m)
    m.mouse.return_value.move.assert_called_once_with(100, 50, duration=0.15)


def test_at_tuple_scales_center_does_not() -> None:
    m = _ctx()
    with patch(
        "vision_workflow.events.builders.move.cached_template_scale",
        return_value=2.0,
    ):
        move().at((40, 60)).pause(0).execute()(m)
    m.mouse.return_value.move.assert_called_once_with(80, 120, duration=0.15)

    m2 = _ctx()
    with (
        patch(
            "vision_workflow.events.builders.move.cached_template_scale",
            return_value=2.0,
        ),
        patch(
            "vision_workflow.events.support.anchor.screen_center",
            return_value=(960, 540),
        ),
    ):
        move().at("center").pause(0).execute()(m2)
    m2.mouse.return_value.move.assert_called_once_with(960, 540, duration=0.15)
