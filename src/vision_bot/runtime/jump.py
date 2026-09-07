"""跳转相关错误。"""

from __future__ import annotations


class JumpTargetError(RuntimeError):
    """跳转 / call 目标不存在，或 return 越界，终止本次运行。"""


class JumpEscape(Exception):
    """runner 内部：goto/return 逃出当前 drive（含 call），由外层 trampoline 接手。"""

    def __init__(self, target_id: str) -> None:
        self.target_id = target_id
        super().__init__(target_id)
