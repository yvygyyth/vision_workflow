"""按模块 id 跳转执行组合式流程。"""

from __future__ import annotations

import importlib
import logging
from pathlib import Path
from typing import Any

from vision_workflow.flow.context import FlowContext
from vision_workflow.models.flow import FlowRunResult, MatchOptions, StepRunResult
from vision_workflow.module import END, FAIL, Module, ModuleGraph
from vision_workflow.promise import Settled

logger = logging.getLogger(__name__)


def load_flow_module(target: str) -> ModuleGraph:
    module_name, _, attr = target.partition(":")
    if module_name.endswith(".py") or "/" in module_name or "\\" in module_name:
        path = Path(module_name).expanduser().resolve()
        import sys

        sys.path.insert(0, str(path.parent))
        mod = importlib.import_module(path.stem)
    else:
        mod = importlib.import_module(module_name)

    if attr:
        obj = getattr(mod, attr)
    elif hasattr(mod, "FLOW"):
        obj = mod.FLOW
    elif hasattr(mod, "MODULES"):
        obj = mod.MODULES
    elif hasattr(mod, "STEPS"):
        obj = mod.STEPS
    elif hasattr(mod, "build_flow"):
        obj = mod.build_flow()
    else:
        raise AttributeError(f"模块 {module_name} 需提供 MODULES / FLOW / build_flow()")

    if callable(obj) and not isinstance(obj, (ModuleGraph, list)):
        obj = obj()

    if isinstance(obj, ModuleGraph):
        return obj

    if isinstance(obj, list):
        entry = getattr(mod, "ENTRY", None) or (obj[0].id if obj else "")
        base_dir = getattr(mod, "BASE_DIR", None)
        if not base_dir and getattr(mod, "__file__", None):
            base_dir = str(Path(mod.__file__).resolve().parents[1])
        return ModuleGraph(
            name=str(getattr(mod, "NAME", None) or getattr(mod, "__name__", "flow")),
            modules=list(obj),
            entry=str(entry),
            dry_run=bool(getattr(mod, "DRY_RUN", False)),
            base_dir=str(base_dir or Path.cwd()),
        )

    raise TypeError(f"期望 ModuleGraph 或 MODULES 列表，得到 {type(obj)}")


class FlowRunner:
    def __init__(
        self,
        flow: ModuleGraph,
        *,
        base_dir: Path | None = None,
        dry_run: bool | None = None,
        entry: str | None = None,
    ) -> None:
        self.flow = flow
        root = Path(flow.base_dir) if flow.base_dir else (base_dir or Path.cwd())
        self.base_dir = root.resolve()
        self.dry_run = flow.dry_run if dry_run is None else dry_run
        self.entry = entry or flow.entry
        self.ctx = FlowContext(
            base_dir=self.base_dir,
            dry_run=self.dry_run,
            defaults=MatchOptions(),
        )

    def run(self, start: str | None = None) -> FlowRunResult:
        current = start or self.entry
        result = FlowRunResult(flow_name=self.flow.name, success=True)
        visits: dict[str, int] = {}
        guard = 0
        max_guard = max(50, len(self.flow.modules) * 20)

        while current not in {END, FAIL, None, ""}:
            guard += 1
            if guard > max_guard:
                result.success = False
                result.message = "疑似死循环，已中止"
                result.feedback = result.message
                break

            try:
                mod = self.flow.get(current)
            except KeyError as exc:
                result.success = False
                result.message = str(exc)
                result.feedback = str(exc)
                break

            if not mod.enabled:
                result.success = False
                result.message = f"模块已禁用: {mod.id}"
                break

            visits[mod.id] = visits.get(mod.id, 0) + 1
            if mod.max_loops and visits[mod.id] > mod.max_loops:
                result.success = False
                result.message = f"模块 [{mod.id}] 超过 max_loops={mod.max_loops}"
                result.feedback = result.message
                break

            result.path.append(mod.id)
            settled, nxt = mod.lifecycle(self.ctx)
            result.steps.append(
                StepRunResult(
                    step_id=mod.id,
                    success=settled.ok,
                    message=settled.error if not settled.ok else "ok",
                    feedback=settled.feedback,
                    value=settled.value,
                )
            )

            # fail 跳到 FAIL 终止符 → 整流程失败
            # fail 跳到其它模块 id → 继续执行（组合跳转）
            if nxt == FAIL:
                result.success = False
                result.message = settled.error or settled.feedback or f"模块失败: {mod.id}"
                result.feedback = settled.feedback or result.message
                break

            if nxt == END:
                if not settled.ok:
                    # 成功分支也能主动 END；若本轮判定失败却指向 END，视为失败结束
                    result.success = False
                    result.message = settled.error or settled.feedback
                    result.feedback = settled.feedback
                break

            current = nxt
        else:
            pass

        if result.success and not result.message:
            feedbacks = [s.feedback for s in result.steps if s.feedback]
            result.message = "流程完成"
            result.feedback = "；".join(feedbacks) if feedbacks else "流程执行成功"
        elif not result.success and not result.feedback:
            result.feedback = result.message

        logger.info(
            "流程结束 success=%s path=%s | %s",
            result.success,
            " → ".join(result.path),
            result.feedback,
        )
        return result

    def run_module(self, module_id: str) -> Settled:
        """只跑某一个模块的生命周期（不自动跳转）。"""
        settled, _nxt = self.flow.get(module_id).lifecycle(self.ctx)
        return settled
