"""Workflow 执行：Flow 内模块跳转，Flow 之间再组合。"""

from __future__ import annotations

import importlib
import logging
import threading
from pathlib import Path

from vision_workflow.flow.context import FlowContext
from vision_workflow.models.flow import FlowRunResult, MatchOptions, StepRunResult
from vision_workflow.module import END, FAIL, Flow, Module, Workflow, resolve_delay_ms, resolve_next
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
    elif hasattr(mod, "FLOW") and isinstance(getattr(mod, "FLOW"), Flow):
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

    def _sleep_ms(self, delay_ms: int, *, reason: str) -> None:
        if delay_ms <= 0 or self._cancelled():
            return
        logger.info("延迟 %sms（%s）", delay_ms, reason)
        self.ctx.sleep(delay_ms / 1000.0)

    def _after_module_delay(self, mod: Module) -> None:
        delay = resolve_delay_ms(mod.config, self.workflow.module_delay_ms)
        self._sleep_ms(delay, reason=f"模块后 {mod.name or mod.id}")

    def _after_flow_delay(self, flow: Flow) -> None:
        delay = resolve_delay_ms(flow.config, self.workflow.flow_delay_ms)
        self._sleep_ms(delay, reason=f"流程后 {flow.display_name}")

    def run(self, start: str | None = None) -> FlowRunResult:
        start_token = start or self.entry
        flow_id, module_start = self._parse_start(start_token)

        result = FlowRunResult(
            flow_name=self.workflow.display_name,
            success=True,
        )
        current_flow = flow_id
        guard = 0
        max_guard = max(50, sum(len(f.modules) for f in self.workflow.flows) * 20)

        while current_flow not in {END, FAIL, None, ""}:
            if self._cancelled():
                result.success = False
                result.message = "用户取消"
                result.feedback = result.message
                break

            guard += 1
            if guard > max_guard:
                result.success = False
                result.message = "疑似死循环，已中止"
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

            flow_ok, last_settled = self._run_flow(
                flow,
                result,
                start_module=module_start if current_flow == flow_id else None,
            )
            module_start = None

            if self._cancelled():
                result.success = False
                result.message = "用户取消"
                result.feedback = result.message
                break

            if not flow_ok and last_settled is None:
                break

            ctx_value = last_settled.value if last_settled else None
            if flow_ok:
                nxt = resolve_next(flow.success, self.ctx, ctx_value, default=END)
                if nxt == FAIL:
                    result.success = False
                    result.message = last_settled.error if last_settled else "流程失败"
                    result.feedback = (
                        (last_settled.feedback if last_settled else None) or result.message
                    )
                    break
                if nxt == END:
                    break
                self._after_flow_delay(flow)
                current_flow = nxt
                continue

            result.success = False
            if last_settled:
                result.message = (
                    last_settled.error
                    or last_settled.feedback
                    or f"流程失败: {flow.display_name}"
                )
                result.feedback = last_settled.feedback or result.message
            nxt = resolve_next(flow.fail, self.ctx, ctx_value, default=END)
            if nxt in {END, FAIL, None, ""}:
                break
            self._after_flow_delay(flow)
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
        settled, _ = mod.run(
            self.ctx,
            default_success=flow.default_success_for(mod.id),
        )
        return settled

    def _parse_start(self, token: str) -> tuple[str, str | None]:
        if "." in token:
            flow_id, module_id = token.split(".", 1)
            return flow_id, module_id
        if token in self.workflow._by_id:
            return token, None
        return self.entry, token

    def _run_flow(
        self,
        flow: Flow,
        result: FlowRunResult,
        *,
        start_module: str | None,
    ) -> tuple[bool, Settled | None]:
        current = start_module or flow.entry
        last: Settled | None = None
        visits: dict[str, int] = {}
        guard = 0
        max_guard = max(20, len(flow.modules) * 20)

        while current not in {END, FAIL, None, ""}:
            if self._cancelled():
                result.success = False
                result.message = "用户取消"
                result.feedback = result.message
                return False, last

            guard += 1
            if guard > max_guard:
                result.success = False
                result.message = f"流程 [{flow.id}] 疑似死循环，已中止"
                result.feedback = result.message
                return False, last

            try:
                mod = flow.get(current)
            except KeyError as exc:
                result.success = False
                result.message = str(exc)
                result.feedback = str(exc)
                return False, last

            if not mod.enabled:
                result.success = False
                result.message = f"模块已禁用: {flow.id}.{mod.id}"
                result.feedback = result.message
                return False, last

            visits[mod.id] = visits.get(mod.id, 0) + 1
            if visits[mod.id] > max_guard:
                result.success = False
                result.message = f"模块 [{flow.id}.{mod.id}] 访问次数过多"
                result.feedback = result.message
                return False, last

            step_id = f"{flow.id}.{mod.id}"
            result.path.append(step_id)
            settled, nxt = mod.run(
                self.ctx,
                default_success=flow.default_success_for(mod.id),
            )
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
                return False, settled

            if nxt == END:
                return settled.ok, settled

            # 还有下一模块：执行后延迟
            self._after_module_delay(mod)
            current = nxt

        return True, last
