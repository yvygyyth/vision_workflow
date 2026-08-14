"""固定枚举：事件状态 / 流程状态 / 控制跳转。

两层状态分开（即便字面值相同也不混用）::
    EventStatus  — 模块 event 返回值，供 Module.on 路由到下一子模块
    FlowStatus   — 流程跑完后的对外状态，供 FlowRouter 路由到下一流程

接口形态均为：状态 → 下一跳（子模块 id / 流程 id / Jump）。
"""

from __future__ import annotations

from enum import Enum
from typing import Any


class EventStatus(str, Enum):
    """事件方法（Module.event）返回的状态。"""

    FULFILLED = "fulfilled"
    REJECTED = "rejected"

    @classmethod
    def from_ok(cls, ok: bool) -> EventStatus:
        return cls.FULFILLED if ok else cls.REJECTED


class FlowStatus(str, Enum):
    """流程跑完后的对外状态（FlowRouter 唯一依据）。"""

    FULFILLED = "fulfilled"
    REJECTED = "rejected"

    @classmethod
    def from_ok(cls, ok: bool) -> FlowStatus:
        return cls.FULFILLED if ok else cls.REJECTED


class Jump(str, Enum):
    """下一跳中的终点哨兵（由状态→下一跳接口产出，非业务 id）。"""

    END = "end"
    FAIL = "fail"


# 事件层常用别名
FULFILLED = EventStatus.FULFILLED
REJECTED = EventStatus.REJECTED

# Jump 别名
END = Jump.END
FAIL = Jump.FAIL

OutcomeKey = EventStatus | str
NextRef = str | Jump


def as_outcome(value: Any) -> OutcomeKey:
    """规范事件 outcome key：已知则收成 EventStatus，否则保留自定义 str。"""
    if isinstance(value, EventStatus):
        return value
    if isinstance(value, Enum):
        value = value.value
    text = str(value)
    try:
        return EventStatus(text)
    except ValueError:
        return text


def as_flow_status(value: FlowStatus | str | Enum) -> FlowStatus:
    """规范流程状态（必须是 FlowStatus；不接受 EventStatus 隐式混用）。"""
    if isinstance(value, FlowStatus):
        return value
    if isinstance(value, EventStatus):
        raise TypeError(
            f"事件状态 {value!r} 不能直接当作流程状态；请用 FlowStatus.from_ok(...) 或显式 FlowStatus"
        )
    if isinstance(value, Enum):
        return FlowStatus(str(value.value))
    return FlowStatus(str(value))


def as_next(value: NextRef | None) -> NextRef:
    """规范下一跳：Jump 或业务 id 字符串。"""
    if value is None or value == "":
        return Jump.END
    if isinstance(value, Jump):
        return value
    if isinstance(value, Enum):
        value = value.value
    text = str(value)
    try:
        return Jump(text)
    except ValueError:
        return text


def is_terminal(target: NextRef | None) -> bool:
    """是否结束当前层级（模块环或流程环）。"""
    return isinstance(as_next(target), Jump)


def is_fail(target: NextRef | None) -> bool:
    return as_next(target) is Jump.FAIL
