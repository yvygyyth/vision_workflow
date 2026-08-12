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

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from vision_workflow.flow.context import FlowContext
from vision_workflow.models.flow import MatchOptions, MatchResult

END = "end"
FAIL = "fail"

# 常用可能性 key（约定，非强制）
OK = "ok"
MISS = "miss"

DEFAULT_MODULE_DELAY_MS = 100
DEFAULT_FLOW_DELAY_MS = 200

EventFn = Callable[["ModuleContext"], str]
OutcomeFn = Callable[["ModuleContext"], str]
NextRef = str | Callable[[FlowContext, Any], str] | None


def resolve_next(ref: NextRef, ctx: FlowContext, value: Any, *, default: str = END) -> str:
    if ref is None:
        return default
    if callable(ref):
        return str(ref(ctx, value) or default)
    return str(ref)


def resolve_delay_ms(config: dict[str, Any] | None, default: int) -> int:
    """读取 config['delay_ms']；未配置则用 default。单位毫秒。"""
    if config and "delay_ms" in config:
        return max(0, int(config["delay_ms"]))
    return max(0, int(default))


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
    config: dict[str, Any] = field(default_factory=dict)
    # 常用: delay_ms / retry / retry_delay_ms / retry_on

    def __post_init__(self) -> None:
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
    config: dict[str, Any] = field(default_factory=dict)
    # 常用: delay_ms / retry / retry_delay_ms

    _by_id: dict[str, Module] = field(init=False, repr=False)
    _next_default: dict[str, str] = field(init=False, repr=False)

    def __post_init__(self) -> None:
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
    module_delay_ms: int = DEFAULT_MODULE_DELAY_MS  # 模块执行后、进入下一模块前
    flow_delay_ms: int = DEFAULT_FLOW_DELAY_MS  # 流程执行后、进入下一流程前
    config: dict[str, Any] = field(default_factory=dict)

    _by_id: dict[str, Flow] = field(init=False, repr=False)

    def __post_init__(self) -> None:
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
