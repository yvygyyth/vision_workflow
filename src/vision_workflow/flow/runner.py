"""Workflow 执行器。"""

from __future__ import annotations

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
from vision_workflow.module import Flow, Workflow
from vision_workflow.promise import Settled
from vision_workflow.status import (
    EventStatus,
    NextRef,
    as_next,
    is_stop,
)

logger = logging.getLogger(__name__)


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
        self.entry = workflow.entry or workflow.nodes[0].flow.id
        self.cancel_event = cancel_event
        self.ctx = FlowContext(
            base_dir=self.base_dir,
            defaults=MatchOptions(),
        )

    def _cancelled(self) -> bool:
        return self.cancel_event is not None and self.cancel_event.is_set()

    def _wait_start_delay(self, result: FlowRunResult) -> bool:
        """启动前延迟；可取消。返回 False 表示已取消并写好 result。"""
        delay_ms = max(0, int(self.workflow.config.start_delay_ms))
        if delay_ms <= 0:
            return True
        logger.info("启动延迟 %sms", delay_ms)
        remaining = delay_ms / 1000.0
        while remaining > 0:
            if self._cancelled():
                result.success = False
                result.message = "用户取消"
                result.feedback = result.message
                return False
            step = min(0.05, remaining)
            self.ctx.sleep(step)
            remaining -= step
        if self._cancelled():
            result.success = False
            result.message = "用户取消"
            result.feedback = result.message
            return False
        return True

    def run(self, start: str | None = None) -> FlowRunResult:
        start_token = start or self.entry
        flow_id, module_start = self._parse_start(start_token)

        result = FlowRunResult(
            flow_name=self.workflow.display_name,
            success=True,
        )
        if not self._wait_start_delay(result):
            return result
        current_flow: NextRef = flow_id

        while not is_stop(current_flow):
            if self._cancelled():
                result.success = False
                result.message = "用户取消"
                result.feedback = result.message
                break

            assert current_flow is not None
            flow_key = current_flow
            try:
                flow = self.workflow.get(flow_key)
            except KeyError as exc:
                result.success = False
                result.message = str(exc)
                result.feedback = str(exc)
                break

            logger.info("流程开始 (%s)", flow.log_label)
            start_for_attempt = module_start if flow_key == flow_id else None
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

            nxt = as_next(scope.next_flow_id)
            if settled.ok:
                if is_stop(nxt):
                    break
                current_flow = nxt
                continue

            result.success = False
            result.message = (
                settled.error or settled.feedback or f"流程失败: {flow.log_label}"
            )
            result.feedback = settled.feedback or result.message
            if is_stop(nxt):
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
        """跑完一轮流程内模块。"""
        current: NextRef = start_module or flow.entry
        last = Settled.reject("空流程")

        while not is_stop(current):
            if self._cancelled():
                return Settled.reject("用户取消", feedback="用户取消")

            assert current is not None
            module_id = current
            try:
                mod = flow.get(module_id)
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
            nxt = as_next(nxt)
            last = settled
            result.steps.append(
                StepRunResult(
                    step_id=step_id,
                    success=settled.ok,
                    message=settled.error if not settled.ok else EventStatus.FULFILLED.value,
                    feedback=settled.feedback,
                    value=settled.value,
                )
            )

            if not settled.ok:
                return settled

            if is_stop(nxt):
                return settled

            current = nxt

        return last
