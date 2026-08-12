"""三级组合：Module → Flow → Workflow。

Module（最小节点）::
    id + event → 成功跳转 / 失败跳转
    success 可省略：默认下一模块；最后一个默认结束流程
    fail 可省略：默认结束当前流程

Flow::
    若干 Module 组成一个流程

Workflow::
    若干 Flow 组成复杂流程
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from vision_workflow.flow.context import FlowContext
from vision_workflow.promise import Settled

logger = logging.getLogger(__name__)

END = "end"
FAIL = "fail"

DEFAULT_MODULE_DELAY_MS = 100
DEFAULT_FLOW_DELAY_MS = 200

EventFn = Callable[[FlowContext], Any]
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
class Module:
    """最小一级节点：只做事，按事件结果跳转。"""

    id: str
    event: EventFn
    success: NextRef = None  # None → 流程内下一个模块；末尾则为 END
    fail: NextRef | None = None  # None → 结束当前流程（END）
    name: str = ""
    enabled: bool = True
    config: dict[str, Any] = field(default_factory=dict)
    # 常用: delay_ms / retry / retry_delay_ms


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
    _next_success: dict[str, str] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        ids = [m.id for m in self.modules]
        if len(ids) != len(set(ids)):
            raise ValueError(f"流程 [{self.id}] 模块 id 必须唯一: {ids}")
        self._by_id = {m.id: m for m in self.modules}
        if self.entry not in self._by_id:
            raise KeyError(f"流程 [{self.id}] 入口模块不存在: {self.entry}")
        # success 未写时：默认下一模块；最后一个默认 END
        self._next_success = {}
        for i, m in enumerate(self.modules):
            if i + 1 < len(self.modules):
                self._next_success[m.id] = self.modules[i + 1].id
            else:
                self._next_success[m.id] = END

    def default_success_for(self, module_id: str) -> str:
        return self._next_success.get(module_id, END)

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

    def flow_choices(self) -> list[tuple[str, str]]:
        """UI 用：(display_name, flow_id)。"""
        return [(f.display_name, f.id) for f in self.flows]


def goto(target_id: str) -> Callable[[FlowContext, Any], str]:
    def _goto(_ctx: FlowContext, _value: Any = None) -> str:
        return target_id

    return _goto
