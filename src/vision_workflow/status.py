"""固定枚举：事件状态 / 流程状态。

两层状态分开（即便字面值相同也不混用）::
    EventStatus  — 模块 event 返回值，供 Module.on 路由到下一子模块
    FlowStatus   — 流程跑完后的对外状态，供 FlowRouter 路由到下一流程

接口形态均为：状态 → 下一跳 id；返回 None 表示本层结束（无下一跳）。
默认 FlowRouter：fulfilled → 顺序下一个 Flow，rejected → 结束（None）。
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


# 事件层常用别名
FULFILLED = EventStatus.FULFILLED
REJECTED = EventStatus.REJECTED

OutcomeKey = EventStatus | str
# 下一跳：业务 id；None = 本层结束
NextRef = str | None

_OUTCOME_LABELS: dict[EventStatus, str] = {
    EventStatus.FULFILLED: "成功",
    EventStatus.REJECTED: "失败",
}


def outcome_label(value: Any) -> str:
    """日志/反馈用的 outcome 文案（避免 f-string 打出 EventStatus.XXX）。"""
    key = as_outcome(value)
    if isinstance(key, EventStatus):
        return _OUTCOME_LABELS.get(key, key.value)
    return str(key)


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


def as_next(value: NextRef | Any) -> NextRef:
    """规范下一跳：业务 id 或 None（结束）。"""
    if value is None:
        return None
    if isinstance(value, Enum):
        value = value.value
    text = str(value).strip()
    return text or None


def is_stop(target: NextRef | Any) -> bool:
    """是否结束当前层级（无下一跳）。"""
    return as_next(target) is None
