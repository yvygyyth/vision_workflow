"""三级组合：Module → Flow → Workflow。

Module（最小节点）::
    id + event + on
    event 必须返回 on 中的某个 key；否则报错结束当前流程
    on[key] 为该可能性对应的处理函数，返回下一模块 id（或 END / FAIL）

Flow::
    若干 Module 组成一个流程

Workflow::
    若干 Flow 组成复杂流程
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Any, TypeVar

from vision_workflow.flow.context import FlowContext
from vision_workflow.models.flow import MatchOptions, MatchResult

END = "end"
FAIL = "fail"

# 常用可能性 key（约定，非强制）
OK = "ok"
MISS = "miss"

EventFn = Callable[["ModuleContext"], str]
OutcomeFn = Callable[["ModuleContext"], str]
NextRef = str | Callable[[FlowContext, Any], str] | None

_ConfigT = TypeVar("_ConfigT")


def resolve_next(ref: NextRef, ctx: FlowContext, value: Any, *, default: str = END) -> str:
    if ref is None:
        return default
    if callable(ref):
        return str(ref(ctx, value) or default)
    return str(ref)


@dataclass
class ModuleConfig:
    """模块级 config：延迟 / 重试。"""

    delay_ms: int = 0
    """成功且还将继续下一模块时的等待（毫秒）；0 则回退 WorkflowConfig.delay_ms。"""
    retry: int = 0
    """失败或命中 retry_on 后的重试次数（总尝试 = 1 + retry）。"""
    retry_delay_ms: int = 0
    """两次重试之间的等待（毫秒）。"""
    retry_on: list[str] = field(default_factory=list)
    """哪些 outcome key 也触发重试（默认仅异常 / 非法 key）。"""


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
    cancelled: Callable[[], bool] = field(default=lambda: False)
    # event 产出：key 为可能性；value 为附带载荷（如 MatchResult）
    key: str | None = None
    value: Any = None

    # ----- FlowContext 能力透传 -----

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

    def click_image(self, image: str | Path, **find_kwargs) -> MatchResult:
        return self.ctx.click_image(image, **find_kwargs)

    def sleep(self, seconds: float) -> None:
        self.ctx.sleep(seconds)

    def log(self, message: str, *args) -> None:
        self.ctx.log(message, *args)

    # ----- 跳转辅助（供 on[*] 使用）-----

    def next(self) -> str:
        """流程内默认下一模块；末尾为 END。"""
        return self.flow.default_next_for(self.module.id)

    def goto(self, module_id: str) -> str:
        return module_id

    def again(self) -> str:
        """自循环：回到当前模块。"""
        return self.module.id

    def end(self) -> str:
        return END

    def fail(self) -> str:
        """结束当前流程并标记失败。"""
        return FAIL


def onward(m: ModuleContext) -> str:
    """常用 outcome：进入默认下一模块。"""
    return m.next()


def abort(m: ModuleContext) -> str:
    """常用 outcome：失败结束当前流程。"""
    return m.fail()


def to(module_id: str) -> OutcomeFn:
    """常用 outcome 工厂：跳到指定模块。"""

    def _go(_m: ModuleContext) -> str:
        return module_id

    return _go


@dataclass
class Module:
    """最小一级节点：event 产出可能性 key，由 on[key] 决定下一跳。"""

    id: str
    event: EventFn
    on: dict[str, OutcomeFn]
    name: str = ""
    enabled: bool = True
    config: ModuleConfig = field(default_factory=ModuleConfig)

    def __post_init__(self) -> None:
        self.config = _coerce_config(ModuleConfig, self.config)
        if not self.on:
            raise ValueError(f"模块 [{self.id}] 必须提供非空 on（可能性 → 处理函数）")
        bad = [k for k, fn in self.on.items() if not callable(fn)]
        if bad:
            raise TypeError(f"模块 [{self.id}] on 的值必须是函数，非法 key: {bad}")


@dataclass
class Flow:
    """二级：由模块组成的流程。"""

    id: str
    modules: list[Module]
    entry: str
    success: NextRef = END  # 本流程成功结束后，下一个流程 id
    fail: NextRef | None = None  # 本流程失败后；None → 结束整个工作流
    name: str = ""  # UI / 日志展示名；空则回退为 id
    config: FlowConfig = field(default_factory=FlowConfig)

    _by_id: dict[str, Module] = field(init=False, repr=False)
    _next_default: dict[str, str] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.config = _coerce_config(FlowConfig, self.config)
        ids = [m.id for m in self.modules]
        if len(ids) != len(set(ids)):
            raise ValueError(f"流程 [{self.id}] 模块 id 必须唯一: {ids}")
        self._by_id = {m.id: m for m in self.modules}
        if self.entry not in self._by_id:
            raise KeyError(f"流程 [{self.id}] 入口模块不存在: {self.entry}")
        # 列表顺序：默认下一模块；最后一个默认 END
        self._next_default = {}
        for i, m in enumerate(self.modules):
            if i + 1 < len(self.modules):
                self._next_default[m.id] = self.modules[i + 1].id
            else:
                self._next_default[m.id] = END

    def default_next_for(self, module_id: str) -> str:
        return self._next_default.get(module_id, END)

    @property
    def display_name(self) -> str:
        return self.name.strip() or self.id

    def get(self, module_id: str) -> Module:
        if module_id not in self._by_id:
            raise KeyError(
                f"流程 [{self.id}] 未知模块: {module_id}，可选: {list(self._by_id)}"
            )
        return self._by_id[module_id]


@dataclass
class Workflow:
    """三级：由流程组成的复杂流程。"""

    flows: list[Flow]
    entry: str
    id: str = "workflow"
    name: str = ""  # UI 展示名；空则回退为 id
    base_dir: str | None = None
    config: WorkflowConfig = field(default_factory=WorkflowConfig)

    _by_id: dict[str, Flow] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.config = _coerce_config(WorkflowConfig, self.config)
        ids = [f.id for f in self.flows]
        if len(ids) != len(set(ids)):
            raise ValueError(f"流程 id 必须唯一: {ids}")
        self._by_id = {f.id: f for f in self.flows}
        if self.entry not in self._by_id:
            raise KeyError(f"入口流程不存在: {self.entry}，可选: {list(self._by_id)}")

    @property
    def display_name(self) -> str:
        return self.name.strip() or self.id

    def get(self, flow_id: str) -> Flow:
        if flow_id not in self._by_id:
            raise KeyError(f"未知流程: {flow_id}，可选: {list(self._by_id)}")
        return self._by_id[flow_id]
