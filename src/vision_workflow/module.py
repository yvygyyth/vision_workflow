"""三级组合：Module → Flow → Workflow。

Module（最小节点）::
    id + event + on
    event 必须返回 on 中的某个 key（EventStatus 或自定义 str）
    on[key] 返回下一模块 id；None 表示本流程结束
    常用助手：onward / abort / back / to(...)
    back 按运行时路径回上一步（见 FlowContext.module_trail）

Flow::
    若干 Module 组成一个流程；结束时用 settled.key 作 FlowRouter 路由
    （内置 fulfilled/rejected，也可自定义 str）

Workflow::
    若干 FlowNode（flow + 可选 router）组成复杂流程
    router 按 FlowOutcomeKey 决定下一流程 id；None 表示工作流结束
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
    FlowOutcomeKey,
    FlowStatus,
    NextRef,
    OutcomeKey,
    as_flow_outcome,
    as_next,
    as_outcome,
    is_stop,
)

EventFn = Callable[["ModuleContext"], OutcomeKey]
OutcomeFn = Callable[["ModuleContext"], NextRef]
FlowHook = Callable[[FlowContext], None]
"""Flow 生命周期钩子签名。"""

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
class FlowLifecycle:
    """流程级生命周期钩子。"""

    on_enter: FlowHook | None = None
    """本 Flow 模块开始跑之前调用。"""
    on_exit: FlowHook | None = None
    """本 Flow 结束后必定调用（成功 / 失败 / 取消）。"""


@dataclass
class WorkflowLifecycle:
    """工作流级生命周期钩子（整次 run 进/出一次）。"""

    on_enter: FlowHook | None = None
    """启动延迟之后、跑第一个 Flow 之前调用（如绑定局内背包状态）。"""
    on_exit: FlowHook | None = None
    """整次工作流结束时必定调用（成功 / 失败 / 取消；如清理背包状态）。"""


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
    """传给 event 与 on[*] 的运行时上下文（识图 / vars / 导航；键鼠、日志、sleep 请用独立 API）。"""

    ctx: FlowContext
    module: Module
    flow: Flow
    workflow: Workflow
    cancelled: Callable[[], bool] = field(default_factory=lambda: (lambda: False))
    key: OutcomeKey | None = None
    value: Any = None
    reason: str = ""
    """event 可写入的可读原因（如识图未找到），供反馈使用。"""
    used_back: bool = False
    """本步 on[*] 是否走了 back()；为 True 时不把当前模块写入 trail。"""

    @property
    def base_dir(self) -> Path:
        return self.ctx.base_dir

    @property
    def vars(self) -> dict:
        return self.ctx.vars

    @property
    def params(self) -> dict:
        """当前 Flow 合并后的入参（Flow 默认 ⊕ FlowNode 传入）。"""
        return self.ctx.params

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
        region_fit: bool | None = None,
        grayscale: bool | None = None,
        match: MatchOptions | None = None,
    ) -> MatchResult:
        return self.ctx.find(
            image,
            threshold=threshold,
            timeout=timeout,
            interval=interval,
            region=region,
            region_fit=region_fit,
            grayscale=grayscale,
            match=match,
        )

    def next(self) -> NextRef:
        """流程内默认下一模块；末尾为 None（结束本流程）。"""
        return self.flow.default_next_for(self.module.id)

    def goto(self, module_id: str) -> NextRef:
        return module_id

    def again(self) -> NextRef:
        """自循环：回到当前模块。"""
        return self.module.id

    def back(self) -> NextRef:
        """回到运行时上一步（本 Flow 内刚成功离开的模块）；无上一步则结束流程。"""
        self.used_back = True
        trail = self.ctx.module_trail
        if not trail:
            return None
        return trail.pop()

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


def back(m: ModuleContext) -> NextRef:
    """常用 outcome：回到运行时上一步；入口步失败则结束（配合 REJECTED）。"""
    return m.back()


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
    params: dict[str, Any] = field(default_factory=dict)
    """硬编码默认入参；运行时与 FlowNode.params 合并（传入优先）。"""
    config: FlowConfig = field(default_factory=FlowConfig)
    lifecycle: FlowLifecycle = field(default_factory=FlowLifecycle)
    """进入 / 退出钩子（成功、失败、取消都会走 on_exit）。"""

    _by_id: dict[str, Module] = field(init=False, repr=False)
    _next_default: dict[str, NextRef] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.config = _coerce_config(FlowConfig, self.config)
        self.lifecycle = _coerce_config(FlowLifecycle, self.lifecycle)
        self.params = dict(self.params or {})
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
    """按 FlowOutcomeKey 决定下一流程 id；None 表示结束。与 Flow 定义独立。

    内置 FlowStatus.FULFILLED / REJECTED，也可使用自定义 str（与 Module.on 对称）。
    """

    on: dict[FlowOutcomeKey, NextRef] = field(default_factory=dict)

    def __post_init__(self) -> None:
        normalized: dict[FlowOutcomeKey, NextRef] = {}
        for key, target in self.on.items():
            normalized[as_flow_outcome(key)] = as_next(target)
        self.on = normalized

    def next(self, status: FlowOutcomeKey) -> NextRef:
        status = as_flow_outcome(status)
        if status not in self.on:
            return None
        return as_next(self.on[status])


@dataclass
class FlowNode:
    """Workflow 中的一格：Flow + 可选路由接口（不传则用默认：成功下一个 / 失败结束）。"""

    flow: Flow
    router: FlowRouter | None = None
    params: dict[str, Any] = field(default_factory=dict)
    """本次编排传入的入参，覆盖 Flow.params 同名键。"""

    def __post_init__(self) -> None:
        self.params = dict(self.params or {})


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
    lifecycle: WorkflowLifecycle = field(default_factory=WorkflowLifecycle)
    """整次 run 的进入 / 退出钩子。"""

    _by_id: dict[str, Flow] = field(init=False, repr=False)
    _nodes_by_id: dict[str, FlowNode] = field(init=False, repr=False)
    _routers: dict[str, FlowRouter] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.config = _coerce_config(WorkflowConfig, self.config)
        self.lifecycle = _coerce_config(WorkflowLifecycle, self.lifecycle)
        if not self.nodes:
            raise ValueError("Workflow.nodes 不能为空")

        ids = [n.flow.id for n in self.nodes]
        if len(ids) != len(set(ids)):
            raise ValueError(f"流程 id 必须唯一: {ids}")
        self._by_id = {n.flow.id: n.flow for n in self.nodes}
        self._nodes_by_id = {n.flow.id: n for n in self.nodes}

        if self.entry is None:
            self.entry = self.nodes[0].flow.id
        if self.entry not in self._by_id:
            raise KeyError(f"入口流程不存在: {self.entry}，可选: {list(self._by_id)}")

        self._routers = {}
        for i, node in enumerate(self.nodes):
            default_next: NextRef = (
                self.nodes[i + 1].flow.id if i + 1 < len(self.nodes) else None
            )
            on: dict[FlowOutcomeKey, NextRef] = {}
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
                flow_id = target.split(".", 1)[0] if "." in target else target
                if flow_id not in self._by_id:
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

    def node_for(self, flow_id: str) -> FlowNode:
        if flow_id not in self._nodes_by_id:
            raise KeyError(f"未知流程节点: {flow_id}，可选: {list(self._nodes_by_id)}")
        return self._nodes_by_id[flow_id]

    def merged_params_for(self, flow_id: str) -> dict[str, Any]:
        """Flow 默认参数 ⊕ FlowNode 传入（传入优先）。"""
        flow = self.get(flow_id)
        node = self.node_for(flow_id)
        return {**flow.params, **node.params}

    def router_for(self, flow_id: str) -> FlowRouter:
        if flow_id not in self._routers:
            raise KeyError(f"未知流程路由: {flow_id}，可选: {list(self._routers)}")
        return self._routers[flow_id]

    def resolve_next(self, flow_id: str, status: FlowOutcomeKey) -> NextRef:
        return self.router_for(flow_id).next(status)
