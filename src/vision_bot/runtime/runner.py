"""流程执行器。"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from vision_bot.runtime.cancel import CancelledError
from vision_bot.runtime.context import RunContext
from vision_bot.runtime.flow import Flow
from vision_bot.runtime.jump import Jump, JumpTargetError
from vision_bot.runtime.module import Module
from vision_bot.runtime.registry import FlowRegistry
from vision_bot.runtime.result import Result

logger = logging.getLogger(__name__)


@dataclass
class RunReport:
    success: bool
    outcome: str = ""
    message: str = ""
    path: list[str] = field(default_factory=list)


@dataclass
class _Resume:
    flow: Flow
    child_index: int


@dataclass
class _FlowAdvance:
    flow: Flow
    start_index: int


class Runner:
    def __init__(self, ctx: RunContext, registry: FlowRegistry) -> None:
        self.ctx = ctx
        self.registry = registry
        self.path: list[str] = []
        self._call_stack: list[_Resume] = []

    def goto(self, target_id: str) -> None:
        self.registry.get(target_id)
        raise Jump("goto", target_id)

    def call(self, target_id: str) -> None:
        self.registry.get(target_id)
        raise Jump("call", target_id)

    def run_flow(self, flow: Flow) -> Result:
        try:
            return self._run_flow(flow)
        except JumpTargetError as exc:
            return Result.fail(str(exc))

    def _try_relocate(self, flow: Flow) -> str | None:
        for rule in flow.relocate:
            self.ctx.check_cancelled()
            target = rule(self.ctx)
            if target:
                return target
        return None

    def _run_flow(self, flow: Flow) -> Result:
        logger.info("[%s]", flow.name)
        self.path.append(flow.id)
        self.ctx.check_cancelled()

        entry = self._try_relocate(flow)
        if entry:
            result = self._run_subtree(entry)
            self.path.pop()
            return result

        result = self._run_flow_children(flow, 0)
        self.path.pop()
        return result

    def _run_flow_children(self, flow: Flow, start_index: int) -> Result:
        for i in range(start_index, len(flow.children)):
            self.ctx.check_cancelled()
            result = self._run_node(flow.children[i], parent_flow=flow, child_index=i)
            outcome = self._consume_node_result(flow, i, result)
            if outcome is not None:
                return outcome
        return Result.success()

    def _consume_node_result(self, flow: Flow, child_index: int, result: Result | _FlowAdvance) -> Result | None:
        if isinstance(result, _FlowAdvance):
            return self._run_flow_children(result.flow, result.start_index)
        if not result.ok:
            recovery = self._try_relocate(flow)
            if recovery:
                rec = self._run_subtree(recovery)
                if not rec.ok:
                    return rec
                retry = self._run_node(flow.children[child_index], parent_flow=flow, child_index=child_index)
                return self._consume_node_result(flow, child_index, retry)
            return result
        return None

    def _run_node(self, node: Flow | Module, *, parent_flow: Flow, child_index: int) -> Result | _FlowAdvance:
        if isinstance(node, Flow):
            return self._run_flow(node)

        logger.info("[%s]", node.name)
        self.path.append(node.id)
        self.ctx.check_cancelled()
        try:
            result = node.active(self.ctx)
        except Jump as jump:
            self.path.pop()
            return self._handle_jump(jump, parent_flow=parent_flow, child_index=child_index)
        except CancelledError:
            self.path.pop()
            return Result.fail("用户取消")
        self.path.pop()

        if not result.ok:
            return result
        return Result.success()

    def _handle_jump(self, jump: Jump, *, parent_flow: Flow, child_index: int) -> Result | _FlowAdvance:
        if jump.kind == "call":
            self._call_stack.append(_Resume(flow=parent_flow, child_index=child_index + 1))
        result = self._run_subtree(jump.target_id)
        if not result.ok:
            return result
        if jump.kind == "call":
            resume = self._call_stack.pop()
            return _FlowAdvance(resume.flow, resume.child_index)
        return self._continue_after_node(jump.target_id)

    def _run_subtree(self, node_id: str) -> Result:
        node = self.registry.get(node_id)
        if isinstance(node, Module):
            logger.info("[%s]", node.name)
            self.path.append(node.id)
            self.ctx.check_cancelled()
            try:
                result = node.active(self.ctx)
            except Jump as jump:
                self.path.pop()
                parent_id = self.registry.parent_flow[node_id]
                parent = self.registry.get(parent_id)
                assert isinstance(parent, Flow)
                idx = self.registry.child_index[node_id]
                handled = self._handle_jump(jump, parent_flow=parent, child_index=idx)
                if isinstance(handled, _FlowAdvance):
                    return self._run_flow_children(handled.flow, handled.start_index)
                return handled
            except CancelledError:
                self.path.pop()
                return Result.fail("用户取消")
            self.path.pop()
            return result
        return self._run_flow(node)

    def _continue_after_node(self, node_id: str) -> Result | _FlowAdvance:
        nxt = self.registry.next_sibling_index(node_id)
        if nxt is not None:
            parent_id, index = nxt
            parent = self.registry.get(parent_id)
            assert isinstance(parent, Flow)
            return _FlowAdvance(parent, index)
        parent_id = self.registry.parent_flow.get(node_id)
        if parent_id is None:
            return Result.success()
        parent = self.registry.get(parent_id)
        assert isinstance(parent, Flow)
        return _FlowAdvance(parent, len(parent.children))


def run_root(flow: Flow, ctx: RunContext, *, loop: bool = False) -> RunReport:
    registry = FlowRegistry.build(flow)
    runner = Runner(ctx, registry)
    ctx._flow_registry = registry
    ctx._runner = runner

    while not ctx.cancelled():
        result = runner.run_flow(flow)
        if not result.ok:
            if ctx.cancelled():
                return RunReport(success=False, message="用户取消", path=runner.path)
            return RunReport(success=False, message=result.message or "执行失败", path=runner.path)
        if not loop:
            return RunReport(success=True, message="完成", path=runner.path)

    return RunReport(success=False, message="用户取消", path=runner.path)
