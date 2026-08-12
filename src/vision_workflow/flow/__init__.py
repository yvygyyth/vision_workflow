"""Workflow 执行：Flow 内模块跳转，Flow 之间再组合。"""

from __future__ import annotations

import importlib
import logging
import threading
from pathlib import Path

from vision_workflow.flow.context import FlowContext
from vision_workflow.middleware import (
    FlowScope,
    ModuleScope,
    build_flow_middlewares,
    execute_module,
    run_flow_onion,
)
from vision_workflow.models.flow import FlowRunResult, MatchOptions, StepRunResult
from vision_workflow.module import END, FAIL, Flow, Workflow
from vision_workflow.paths import project_root
from vision_workflow.promise import Settled

logger = logging.getLogger(__name__)


def load_flow_module(target: str) -> Workflow:
    """加载配置模块，返回 Workflow。

    配置可提供：
    - WORKFLOW: Workflow
    - FLOWS + ENTRY: 流程列表
    - MODULES + ENTRY: 单流程快捷写法（自动包成一个 Workflow）
    """
    module_name, _, attr = target.partition(":")
    if module_name.endswith(".py") or "/" in module_name or "\\" in module_name:
        path = Path(module_name).expanduser().resolve()
        import sys

        sys.path.insert(0, str(path.parent))
        mod = importlib.import_module(path.stem)
    else:
        mod = importlib.import_module(module_name)

    base_dir = getattr(mod, "BASE_DIR", None) or str(project_root())
    name = str(getattr(mod, "NAME", None) or getattr(mod, "__name__", "workflow"))

    if attr:
        obj = getattr(mod, attr)
    elif hasattr(mod, "WORKFLOW"):
        obj = mod.WORKFLOW
    elif hasattr(mod, "FLOWS"):
        entry = getattr(mod, "ENTRY", None)
        if not entry:
            raise AttributeError(f"模块 {module_name} 提供 FLOWS 时需同时提供 ENTRY")
        obj = Workflow(
            id=getattr(mod, "WORKFLOW_ID", "main"),
            name=name,
            flows=list(mod.FLOWS),
            entry=str(entry),
            base_dir=str(base_dir or Path.cwd()),
        )
    elif hasattr(mod, "FLOW") and isinstance(mod.FLOW, Flow):
        flow = mod.FLOW
        obj = Workflow(
            id=getattr(mod, "WORKFLOW_ID", "main"),
            name=name,
            flows=[flow],
            entry=flow.id,
            base_dir=str(base_dir or Path.cwd()),
        )
    elif hasattr(mod, "MODULES"):
        entry = getattr(mod, "ENTRY", None) or mod.MODULES[0].id
        flow = Flow(
            id=getattr(mod, "FLOW_ID", "main"),
            name=name,
            modules=list(mod.MODULES),
            entry=str(entry),
            success=END,
            fail=None,
        )
        obj = Workflow(
            id=getattr(mod, "WORKFLOW_ID", "main"),
            name=name,
            flows=[flow],
            entry=flow.id,
            base_dir=str(base_dir or Path.cwd()),
        )
    else:
        raise AttributeError(
            f"模块 {module_name} 需提供 WORKFLOW / FLOWS / FLOW / MODULES"
        )

    if callable(obj) and not isinstance(obj, Workflow):
        obj = obj()

    if not isinstance(obj, Workflow):
        raise TypeError(f"期望 Workflow，得到 {type(obj)}")

    if obj.base_dir is None and base_dir:
        obj.base_dir = str(base_dir)
    if not obj.name:
        obj.name = name
    return obj


class WorkflowRunner:
    """执行 Workflow（流程内模块跳转，流程间再组合）。"""

    def __init__(
        self,
        workflow: Workflow,
        *,
        base_dir: Path | None = None,
        cancel_event: threading.Event | None = None,
    ) -> None:
        self.workflow = workflow
        root = Path(workflow.base_dir) if workflow.base_dir else (base_dir or Path.cwd())
        self.base_dir = root.resolve()
        self.entry = workflow.entry
        self.cancel_event = cancel_event
        self.ctx = FlowContext(
            base_dir=self.base_dir,
            defaults=MatchOptions(),
        )

    def _cancelled(self) -> bool:
        return self.cancel_event is not None and self.cancel_event.is_set()

    def run(self, start: str | None = None) -> FlowRunResult:
        start_token = start or self.entry
        flow_id, module_start = self._parse_start(start_token)

        result = FlowRunResult(
            flow_name=self.workflow.display_name,
            success=True,
        )
        current_flow = flow_id

        while current_flow not in {END, FAIL, ""}:
            if self._cancelled():
                result.success = False
                result.message = "用户取消"
                result.feedback = result.message
                break

            try:
                flow = self.workflow.get(current_flow)
            except KeyError as exc:
                result.success = False
                result.message = str(exc)
                result.feedback = str(exc)
                break

            logger.info("流程开始 (%s)", flow.display_name)
            start_for_attempt = module_start if current_flow == flow_id else None
            module_start = None
            first_shot = {"pending": start_for_attempt, "used": False}

            scope = FlowScope(
                ctx=self.ctx,
                flow=flow,
                workflow=self.workflow,
                cancelled=self._cancelled,
            )

            def _core(flow: Flow = flow) -> Settled:
                start = None
                if not first_shot["used"]:
                    start = first_shot["pending"]
                    first_shot["used"] = True
                return self._run_flow_modules(flow, result, start_module=start)

            settled = run_flow_onion(scope, build_flow_middlewares(scope), _core)

            if self._cancelled():
                result.success = False
                result.message = "用户取消"
                result.feedback = result.message
                break

            nxt = scope.next_flow_id
            if settled.ok:
                if nxt == FAIL:
                    result.success = False
                    result.message = settled.error or "流程失败"
                    result.feedback = settled.feedback or result.message
                    break
                if nxt in {END, ""}:
                    break
                current_flow = nxt
                continue

            result.success = False
            result.message = (
                settled.error or settled.feedback or f"流程失败: {flow.display_name}"
            )
            result.feedback = settled.feedback or result.message
            if nxt in {END, FAIL, ""}:
                break
            current_flow = nxt

        if result.success and not result.message:
            feedbacks = [s.feedback for s in result.steps if s.feedback]
            result.message = "流程完成"
            result.feedback = "；".join(feedbacks) if feedbacks else "流程执行成功"
        elif not result.success and not result.feedback:
            result.feedback = result.message

        logger.info(
            "工作流结束 success=%s path=%s | %s",
            result.success,
            " → ".join(result.path),
            result.feedback,
        )
        return result

    def run_module(self, target: str) -> Settled:
        """只跑某一个模块。格式: module_id 或 flow_id.module_id。"""
        flow: Flow | None = None
        if "." in target:
            flow_id, module_id = target.split(".", 1)
            flow = self.workflow.get(flow_id)
            mod = flow.get(module_id)
        else:
            try:
                flow = self.workflow.get(self.entry)
                mod = flow.get(target)
            except KeyError:
                mod = None
                for candidate in self.workflow.flows:
                    if target in candidate._by_id:
                        flow = candidate
                        mod = candidate.get(target)
                        break
                if mod is None or flow is None:
                    raise KeyError(f"未知模块: {target}") from None
        scope = ModuleScope(
            ctx=self.ctx,
            module=mod,
            flow=flow,
            workflow=self.workflow,
            cancelled=self._cancelled,
        )
        settled, _ = execute_module(scope)
        return settled

    def _parse_start(self, token: str) -> tuple[str, str | None]:
        if "." in token:
            flow_id, module_id = token.split(".", 1)
            return flow_id, module_id
        if token in self.workflow._by_id:
            return token, None
        return self.entry, token

    def _run_flow_modules(
        self,
        flow: Flow,
        result: FlowRunResult,
        *,
        start_module: str | None,
    ) -> Settled:
        """跑完一轮流程内模块（可被流程级 Retry 多次调用）。"""
        current = start_module or flow.entry
        last = Settled.reject("空流程")

        while current not in {END, FAIL, ""}:
            if self._cancelled():
                return Settled.reject("用户取消", feedback="用户取消")

            try:
                mod = flow.get(current)
            except KeyError as exc:
                return Settled.reject(str(exc), feedback=str(exc))

            if not mod.enabled:
                msg = f"模块已禁用: {flow.id}.{mod.id}"
                return Settled.reject(msg, feedback=msg)

            step_id = f"{flow.id}.{mod.id}"
            result.path.append(step_id)
            scope = ModuleScope(
                ctx=self.ctx,
                module=mod,
                flow=flow,
                workflow=self.workflow,
                cancelled=self._cancelled,
            )
            settled, nxt = execute_module(scope)
            last = settled
            result.steps.append(
                StepRunResult(
                    step_id=step_id,
                    success=settled.ok,
                    message=settled.error if not settled.ok else "ok",
                    feedback=settled.feedback,
                    value=settled.value,
                )
            )

            if nxt == FAIL:
                return settled if not settled.ok else Settled.reject("流程 FAIL", value=settled.value)

            if nxt == END:
                if settled.ok:
                    return settled
                return settled

            current = nxt

        return last
