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
    then:
        仅 ``ok=True`` 时有意义：跳到该节点 id（取代旧 ``ctx.goto``）。
        ``ok=False`` 时忽略此字段。
    """

    ok: bool
    message: str = ""
    value: Any = None
    then: str | None = None

    @classmethod
    def success(
        cls,
        message: str = "",
        *,
        value: Any = None,
        then: str | None = None,
    ) -> Result:
        """构造成功结果。"""
        return cls(ok=True, message=message, value=value, then=then)

    @classmethod
    def fail(cls, message: str = "", *, value: Any = None) -> Result:
        """构造失败结果。"""
        return cls(ok=False, message=message, value=value, then=None)

    @property
    def failed(self) -> bool:
        """是否失败，等价于 ``not ok``。"""
        return not self.ok


def normalize_outcome(value: Result | str | None) -> Result | None:
    """将 active / relocate.then 出口归一为 ``None | Result``。

    - ``None`` → ``None``（不跳转；active 侧视为成功继续）
    - ``str`` → ``Result.success(then=str)``
    - ``Result`` → 原样（``ok=False`` 时 ``then`` 视为无效）
    """
    if value is None:
        return None
    if isinstance(value, str):
        return Result.success(then=value)
    if isinstance(value, Result):
        if not value.ok and value.then is not None:
            return Result.fail(value.message, value=value.value)
        return value
    raise TypeError(f"outcome 须为 None | str | Result，收到 {type(value)!r}")
