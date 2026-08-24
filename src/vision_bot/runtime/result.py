"""统一执行结果（actions / runtime / vision / events 共用）。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class Result:
    """步骤或操作的统一返回值。

    Attributes
    ----------
    ok:
        ``True`` 表示成功，``False`` 表示失败。
    message:
        补充说明。失败时为错误原因；成功时通常为空字符串。
    value:
        附加数据。例如识图成功时为 :class:`~vision_bot.core.models.MatchResult`，
        ``find_all`` 成功时为 ``list[MatchResult]``。
    """

    ok: bool
    message: str = ""
    value: Any = None

    @classmethod
    def success(cls, message: str = "", *, value: Any = None) -> Result:
        """构造成功结果。

        Parameters
        ----------
        message:
            可选的成功说明。
        value:
            可选的附加数据。
        """
        return cls(ok=True, message=message, value=value)

    @classmethod
    def fail(cls, message: str = "", *, value: Any = None) -> Result:
        """构造失败结果。

        Parameters
        ----------
        message:
            失败原因，会展示给用户或写入日志。
        value:
            可选的附加数据（如末次识图结果）。
        """
        return cls(ok=False, message=message, value=value)

    @property
    def failed(self) -> bool:
        """是否失败，等价于 ``not ok``。"""
        return not self.ok
