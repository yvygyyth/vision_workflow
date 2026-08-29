"""跳转相关错误。"""

from __future__ import annotations


class JumpTargetError(RuntimeError):
    """跳转 / call 目标不存在，终止本次运行。"""


class ThenEscape(Exception):
    """runner 内部：从 active/call 栈中跳出并执行 then（不对外暴露）。"""

    def __init__(self, target_id: str) -> None:
        self.target_id = target_id
        super().__init__(target_id)
