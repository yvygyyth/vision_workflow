"""Flow 包：上下文 + 执行器。

``from vision_workflow.flow.context`` 可安全导入，不会拉起 Runner/中间件，
从而避免与 ``module`` / ``flows`` 的循环依赖。
"""

from __future__ import annotations

from typing import Any

from vision_workflow.flow.context import FlowContext

__all__ = ["FlowContext", "WorkflowRunner", "load_flow_module"]


def __getattr__(name: str) -> Any:
    if name in {"WorkflowRunner", "load_flow_module"}:
        from vision_workflow.flow import runner

        return getattr(runner, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
