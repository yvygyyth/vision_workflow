"""运行配置（与 Flow 定义分离）。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class RunConfig:
    """一次执行的运行时选项。

    Attributes
    ----------
    entry_id:
        起始节点 id（Flow 或 Module）。``None`` 表示从根 Flow 开头执行。
    loop:
        成功后是否循环执行。
    params:
        覆盖 **entry 所在 Flow** 的 ``params``（UI 由 JSON 解析填入）。
    """

    entry_id: str | None = None
    loop: bool = False
    params: dict[str, Any] = field(default_factory=dict)
