"""相对位移：跨 do() 步骤时应相对当前光标。"""

from unittest.mock import MagicMock, patch

from vision_workflow.input import Mouse


def test_relative_move_falls_back_to_cursor_position() -> None:
    mouse = Mouse()
    api = MagicMock()
    api.position.return_value = (800, 400)
    with patch.object(Mouse, "_api", return_value=api):
        nx, ny = mouse._resolve_xy(-160, 0, relative=True)
    assert (nx, ny) == (640, 400)
    assert mouse._x == 800 and mouse._y == 400
