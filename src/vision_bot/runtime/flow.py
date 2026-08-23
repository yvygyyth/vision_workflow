"""Flow 定义。"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from vision_bot.runtime.context import RunContext
from vision_bot.runtime.types import END, FAIL, OK, OutcomeKey

# 步骤失败且 routes 未命中时：自行截屏识图，返回应跳转的 step id；None 则向父 Flow 冒泡
RelocateFn = Callable[[RunContext], str | None]
# on / routes 的目标：step id、None，或 END 哨兵（结束本 Flow 并向上返回 outcome）
NextRef = str | None | object


@dataclass
class StepResult:
    # 本步业务结果，供父级 on 路由（如 back_to_hub、fight）
    outcome: OutcomeKey = OK
    # 显式下一跳 step id；END 表示结束本 Flow
    next_id: str | None = None
    # True 时 runner 先查 routes，再调 relocate 重定位
    failed: bool = False
    # 失败原因，写入日志 / RunReport
    message: str = ""

    @classmethod
    def ok(cls, *, next_id: str | None = None, outcome: OutcomeKey = OK) -> StepResult:
        return cls(outcome=outcome, next_id=next_id)

    @classmethod
    def fail(cls, message: str = "") -> StepResult:
        return cls(outcome=FAIL, failed=True, message=message)

    @classmethod
    def end(cls, outcome: OutcomeKey) -> StepResult:
        return cls(outcome=outcome, next_id=END)


# 叶子步骤：自行决定是否需要识图/点击
StepFn = Callable[[RunContext], StepResult]


@dataclass
class Flow:
    # Flow 唯一标识，日志与顶层 steps 字典 key 对齐
    id: str
    # 步骤表：key 即 step id；值为 StepFn 或嵌套子 Flow
    steps: dict[str, Flow | StepFn]
    # 进入本 Flow 时第一个执行的 step id
    entry: str
    # 显示名，仅用于日志
    name: str = ""
    # 步骤失败后的画面重定位；None 表示无法识别时直接冒泡
    relocate: RelocateFn | None = None
    # 子 Flow 结束或 StepResult.end 后的出口路由：outcome → step id / END
    on: dict[OutcomeKey, NextRef] = field(default_factory=dict)
    # 单步 outcome 路由：step id → {outcome → 下一 step id}
    routes: dict[str, dict[OutcomeKey, str]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.steps = normalize_steps(self.steps, flow_id=self.id)

    def get(self, step_id: str) -> Flow | StepFn:
        if step_id not in self.steps:
            raise KeyError(f"Flow [{self.id}] 未知步骤: {step_id}")
        return self.steps[step_id]

    def resolve_route(self, step_id: str, outcome: OutcomeKey) -> NextRef | None:
        step_routes = self.routes.get(step_id)
        if not step_routes:
            return None
        return step_routes.get(outcome)


def normalize_steps(raw: dict[str, Flow | StepFn], *, flow_id: str) -> dict[str, Flow | StepFn]:
    out: dict[str, Flow | StepFn] = {}
    for key, val in raw.items():
        if isinstance(val, Flow):
            out[key] = val
        elif callable(val):
            out[key] = val
        else:
            raise TypeError(f"Flow [{flow_id}] 步骤 {key!r} 须为 Flow 或 StepFn")
    return out
