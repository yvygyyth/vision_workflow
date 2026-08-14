"""三级组合：Module → Flow → Workflow。

Module（最小节点）::
    id + event + on
    event 必须返回 on 中的某个 key（EventStatus 或自定义 str）
    on[key] 返回下一模块 id；None 表示本流程结束

Flow::
    若干 Module 组成一个流程；跑完映射为 FlowStatus（经由 settled.ok）

Workflow::
    若干 FlowNode（flow + 可选 router）组成复杂流程
    router 按 FlowStatus 决定下一流程 id；None 表示工作流结束
    缺省接口：fulfilled → 顺序下一个，rejected → 结束
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Any, TypeVar

from vision_workflow.flow.context import FlowContext
from vision_workflow.models.flow import MatchOptions, MatchResult
from vision_workflow.status import (
    FlowStatus,
    NextRef,
    OutcomeKey,
    as_flow_status,
    as_next,
    as_outcome,
    is_stop,
)

EventFn = Callable[["ModuleContext"], OutcomeKey]
OutcomeFn = Callable[["ModuleContext"], NextRef]

_ConfigT = TypeVar("_ConfigT")

DEFAULT_START_DELAY_MS = 2000
"""点开始后默认等待毫秒数。"""


def _log_label(*, id: str, name: str, description: str) -> str:
    """日志用标题：优先 name，有 description 则附上。"""
    title = name.strip() or id
    desc = description.strip()
    return f"{title} — {desc}" if desc else title


@dataclass
class ModuleConfig:
    """模块级 config：延迟 / 重试。"""

    delay_ms: int = 0
    """成功且还将继续下一模块时的等待（毫秒）；0 则回退 WorkflowConfig.delay_ms。"""
    retry: int = 0
    """失败或命中 retry_on 后的重试次数（总尝试 = 1 + retry）。"""
    retry_delay_ms: int = 0
    """两次重试之间的等待（毫秒）。"""
    retry_on: list[OutcomeKey] = field(default_factory=list)
    """哪些 outcome 也触发重试（默认仅异常 / 非法 key）。"""

    def __post_init__(self) -> None:
        self.retry_on = [as_outcome(k) for k in self.retry_on]


@dataclass
class FlowConfig:
    """流程级 config。"""

    delay_ms: int = 0
    """本流程成功且还将进入下一流程时的等待（毫秒）；0 则回退 WorkflowConfig.delay_ms。"""


@dataclass
class WorkflowConfig:
    """复杂流程级 config。"""

    delay_ms: int = 0
    """默认延迟（毫秒）：模块/流程未单独配置 delay_ms 时使用。"""
    start_delay_ms: int = DEFAULT_START_DELAY_MS
    """点开始后、正式执行前的等待（毫秒）。"""


def _coerce_config(cls: type[_ConfigT], value: _ConfigT | Mapping[str, Any] | None) -> _ConfigT:
    if value is None:
        return cls()  # type: ignore[call-arg]
    if isinstance(value, cls):
        return value
    if isinstance(value, Mapping):
        allowed = {f.name for f in fields(cls)}  # type: ignore[arg-type]
        return cls(**{k: v for k, v in value.items() if k in allowed})  # type: ignore[call-arg]
    raise TypeError(f"期望 {cls.__name__} 或 dict，得到 {type(value)}")


@dataclass
class ModuleContext:
    """传给 event 与 on[*] 的运行时上下文，便于扩展自循环等。"""

    ctx: FlowContext
    module: Module
    flow: Flow
    workflow: Workflow
    cancelled: Callable[[], bool] = field(default_factory=lambda: (lambda: False))
    key: OutcomeKey | None = None
    value: Any = None
    reason: str = ""
    """event 可写入的可读原因（如识图未找到），供反馈/日志使用。"""

    @property
    def base_dir(self) -> Path:
        return self.ctx.base_dir

    @property
    def vars(self) -> dict:
        return self.ctx.vars

    def resolve(self, image: str | Path) -> Path:
        return self.ctx.resolve(image)

    def find(
        self,
        image: str | Path,
        *,
        threshold: float | None = None,
        timeout: float | None = None,
        interval: float | None = None,
        region: tuple[int, int, int, int] | None = None,
        grayscale: bool | None = None,
        match: MatchOptions | None = None,
    ) -> MatchResult:
        return self.ctx.find(
            image,
            threshold=threshold,
            timeout=timeout,
            interval=interval,
            region=region,
            grayscale=grayscale,
            match=match,
        )

    def mouse(self):
        return self.ctx.mouse()

    def sleep(self, seconds: float) -> None:
        self.ctx.sleep(seconds)

    def log(self, message: str, *args) -> None:
        self.ctx.log(message, *args)

    def next(self) -> NextRef:
        """流程内默认下一模块；末尾为 None（结束本流程）。"""
        return self.flow.default_next_for(self.module.id)

    def goto(self, module_id: str) -> NextRef:
        return module_id

    def again(self) -> NextRef:
        """自循环：回到当前模块。"""
        return self.module.id

    def end(self) -> None:
        """结束当前流程（成败由 event 状态决定）。"""
        return None

    def fail(self) -> None:
        """结束当前流程（通常配合 REJECTED）。"""
        return None


def onward(m: ModuleContext) -> NextRef:
    """常用 outcome：进入默认下一模块；末尾则结束。"""
    return m.next()


def abort(m: ModuleContext) -> NextRef:
    """常用 outcome：结束当前流程（配合 REJECTED → 流程失败）。"""
    return m.fail()


def to(module_id: str) -> OutcomeFn:
    """常用 outcome 工厂：跳到指定模块。"""

    def _go(_m: ModuleContext) -> NextRef:
        return module_id

    return _go


@dataclass
class Module:
    """最小一级节点：event 产出可能性 key，由 on[key] 决定下一跳。"""

    id: str
    event: EventFn
    on: dict[OutcomeKey, OutcomeFn]
    name: str = ""
    description: str = ""
    enabled: bool = True
    config: ModuleConfig = field(default_factory=ModuleConfig)

    def __post_init__(self) -> None:
        self.config = _coerce_config(ModuleConfig, self.config)
        if not self.on:
            raise ValueError(f"模块 [{self.id}] 必须提供非空 on（可能性 → 处理函数）")
        normalized: dict[OutcomeKey, OutcomeFn] = {}
        for key, fn in self.on.items():
            if not callable(fn):
                raise TypeError(f"模块 [{self.id}] on 的值必须是函数，非法 key: {key}")
            normalized[as_outcome(key)] = fn
        self.on = normalized

    @property
    def display_name(self) -> str:
        return self.name.strip() or self.id

    @property
    def log_label(self) -> str:
        return _log_label(id=self.id, name=self.name, description=self.description)

    def has_outcome(self, key: OutcomeKey | Any) -> bool:
        return as_outcome(key) in self.on

    def handler_for(self, key: OutcomeKey | Any) -> OutcomeFn:
        return self.on[as_outcome(key)]


@dataclass
class Flow:
    """二级：由模块组成的流程（不包含流程间跳转）。"""

    id: str
    modules: list[Module]
    entry: str
    name: str = ""
    description: str = ""
    config: FlowConfig = field(default_factory=FlowConfig)

    _by_id: dict[str, Module] = field(init=False, repr=False)
    _next_default: dict[str, NextRef] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.config = _coerce_config(FlowConfig, self.config)
        ids = [m.id for m in self.modules]
        if len(ids) != len(set(ids)):
            raise ValueError(f"流程 [{self.id}] 模块 id 必须唯一: {ids}")
        self._by_id = {m.id: m for m in self.modules}
        if self.entry not in self._by_id:
            raise KeyError(f"流程 [{self.id}] 入口模块不存在: {self.entry}")
        self._next_default = {}
        for i, m in enumerate(self.modules):
            if i + 1 < len(self.modules):
                self._next_default[m.id] = self.modules[i + 1].id
            else:
                self._next_default[m.id] = None

    def default_next_for(self, module_id: str) -> NextRef:
        return self._next_default.get(module_id)

    @property
    def display_name(self) -> str:
        return self.name.strip() or self.id

    @property
    def log_label(self) -> str:
        return _log_label(id=self.id, name=self.name, description=self.description)

    def get(self, module_id: str) -> Module:
        if module_id not in self._by_id:
            raise KeyError(
                f"流程 [{self.id}] 未知模块: {module_id}，可选: {list(self._by_id)}"
            )
        return self._by_id[module_id]


@dataclass
class FlowRouter:
    """按 FlowStatus 决定下一流程 id；None 表示结束。与 Flow 定义独立。"""

    on: dict[FlowStatus, NextRef] = field(default_factory=dict)

    def __post_init__(self) -> None:
        normalized: dict[FlowStatus, NextRef] = {}
        for key, target in self.on.items():
            normalized[as_flow_status(key)] = as_next(target)
        self.on = normalized

    def next(self, status: FlowStatus) -> NextRef:
        status = as_flow_status(status)
        if status not in self.on:
            return None
        return as_next(self.on[status])


@dataclass
class FlowNode:
    """Workflow 中的一格：Flow + 可选路由接口（不传则用默认：成功下一个 / 失败结束）。"""

    flow: Flow
    router: FlowRouter | None = None


@dataclass
class Workflow:
    """三级：由 FlowNode 组成的复杂流程。"""

    nodes: list[FlowNode]
    entry: str | None = None
    id: str = "workflow"
    name: str = ""
    description: str = ""
    base_dir: str | None = None
    config: WorkflowConfig = field(default_factory=WorkflowConfig)

    _by_id: dict[str, Flow] = field(init=False, repr=False)
    _routers: dict[str, FlowRouter] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.config = _coerce_config(WorkflowConfig, self.config)
        if not self.nodes:
            raise ValueError("Workflow.nodes 不能为空")

        ids = [n.flow.id for n in self.nodes]
        if len(ids) != len(set(ids)):
            raise ValueError(f"流程 id 必须唯一: {ids}")
        self._by_id = {n.flow.id: n.flow for n in self.nodes}

        if self.entry is None:
            self.entry = self.nodes[0].flow.id
        if self.entry not in self._by_id:
            raise KeyError(f"入口流程不存在: {self.entry}，可选: {list(self._by_id)}")

        self._routers = {}
        for i, node in enumerate(self.nodes):
            default_next: NextRef = (
                self.nodes[i + 1].flow.id if i + 1 < len(self.nodes) else None
            )
            on: dict[FlowStatus, NextRef] = {}
            if node.router is not None:
                on.update(node.router.on)
            # 默认接口：成功 → 下一个；失败 → 结束
            on.setdefault(FlowStatus.FULFILLED, default_next)
            on.setdefault(FlowStatus.REJECTED, None)
            router = FlowRouter(on=on)
            for target in router.on.values():
                if is_stop(target):
                    continue
                assert target is not None
                if target not in self._by_id:
                    raise KeyError(
                        f"流程 [{node.flow.id}] 路由目标不存在: {target}，"
                        f"可选: {list(self._by_id)}"
                    )
            self._routers[node.flow.id] = router

    @property
    def display_name(self) -> str:
        return self.name.strip() or self.id

    @property
    def log_label(self) -> str:
        return _log_label(id=self.id, name=self.name, description=self.description)

    @property
    def flows(self) -> list[Flow]:
        return [n.flow for n in self.nodes]

    def get(self, flow_id: str) -> Flow:
        if flow_id not in self._by_id:
            raise KeyError(f"未知流程: {flow_id}，可选: {list(self._by_id)}")
        return self._by_id[flow_id]

    def router_for(self, flow_id: str) -> FlowRouter:
        if flow_id not in self._routers:
            raise KeyError(f"未知流程路由: {flow_id}，可选: {list(self._routers)}")
        return self._routers[flow_id]

    def resolve_next(self, flow_id: str, status: FlowStatus) -> NextRef:
        return self.router_for(flow_id).next(status)
