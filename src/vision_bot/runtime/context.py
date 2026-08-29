"""运行时上下文（单次 run 的会话状态）。"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from vision_bot.runtime.result import Result


@dataclass
class RunContext:
    vars: dict[str, Any] = field(default_factory=dict)
    cancel_event: threading.Event | None = None
    _runner: Any = field(default=None, repr=False)
    _params_stack: list[dict[str, Any]] = field(default_factory=list)
    _pending_pass_params: dict[str, Any] | None = field(default=None, repr=False)
    _entry_flow_id: str = field(default="", repr=False)
    _run_param_overrides: dict[str, Any] = field(default_factory=dict, repr=False)

    def cancelled(self) -> bool:
        return self.cancel_event is not None and self.cancel_event.is_set()

    def check_cancelled(self) -> None:
        from vision_bot.runtime.cancel import raise_if_cancelled
        raise_if_cancelled(self.cancelled)

    @property
    def params(self) -> dict[str, Any]:
        """当前 Flow 作用域内的 params（栈顶）。"""
        if not self._params_stack:
            return {}
        return self._params_stack[-1]

    def pass_params(self, params: dict[str, Any]) -> None:
        """显式传给下一个进入的子 Flow（进入时与 child.params 合并）。"""
        self._pending_pass_params = dict(params)

    def _take_pass_params(self) -> dict[str, Any]:
        passed = self._pending_pass_params or {}
        self._pending_pass_params = None
        return passed

    def enter_flow(self, flow_id: str, flow_params: dict[str, Any]) -> None:
        passed = self._take_pass_params()
        override = self._run_param_overrides if flow_id == self._entry_flow_id else {}
        parent = self._params_stack[-1] if self._params_stack else {}
        # 子 Flow 默认 ← 父级传参 ← pass_params ← entry 运行时覆盖
        self._params_stack.append({**flow_params, **parent, **passed, **override})

    def exit_flow(self) -> None:
        if self._params_stack:
            self._params_stack.pop()

    def call(self, target_id: str) -> Result:
        """同步插入执行目标子树，返回 Result；可继续写后续逻辑。"""
        if self._runner is None:
            raise RuntimeError("call 需要在 run 内调用")
        return self._runner.call(target_id)
