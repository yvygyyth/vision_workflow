"""流程执行器。"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

from vision_bot.core.paths import project_root
from vision_bot.perception.session import bind_perception
from vision_bot.runtime.bind import bind_runtime
from vision_bot.runtime.cancel import CancelledError
from vision_bot.runtime.config import RunConfig
from vision_bot.runtime.context import RunContext
from vision_bot.runtime.flow import Flow
from vision_bot.runtime.jump import JumpTargetError, ThenEscape
from vision_bot.runtime.module import Module
from vision_bot.runtime.registry import FlowRegistry
from vision_bot.runtime.relocate import resolve
from vision_bot.runtime.result import Result, normalize_outcome

logger = logging.getLogger(__name__)


@dataclass
class RunReport:
    success: bool
    message: str = ""
    path: list[str] = field(default_factory=list)


@dataclass
class _FlowAdvance:
    flow: Flow
    start_index: int


class Runner:
    def __init__(self, ctx: RunContext, registry: FlowRegistry, *, root: Flow) -> None:
        self.ctx = ctx
        self.registry = registry
        self.root = root
        self.path: list[str] = []
        self._flow_stack: list[str] = []
        self._call_stack: list[str] = []

    def call(self, target_id: str) -> Result:
        """同步插入执行目标子树，返回其 Result；调用方可继续处理。

        被 call 的工具 Flow 若 relocate 失败且无业务父级，
        则改走**调用方 Flow** 的 relocate。
        若恢复目标落在 call 子树外，抛出 ThenEscape 由外层接管（等同旧 goto）。
        """
        if not self._flow_stack:
            raise RuntimeError("call 必须在 Flow 执行中调用")
        self.registry.get(target_id)
        self._call_stack.append(self._flow_stack[-1])
        try:
            return self._run_subtree(target_id)
        finally:
            self._call_stack.pop()

    def run_flow(self, flow: Flow) -> Result:
        try:
            return self._run_flow(flow)
        except JumpTargetError as exc:
            return Result.fail(str(exc))

    def run_from(self, entry_id: str) -> Result:
        node = self.registry.get(entry_id)
        if isinstance(node, Flow) and entry_id == self.root.id:
            return self.run_flow(node)
        parent, start_index = self.registry.entry_point(entry_id)
        self.ctx.enter_flow(parent.id, parent.params)
        try:
            return self._run_flow_children(parent, start_index)
        except JumpTargetError as exc:
            return Result.fail(str(exc))
        finally:
            self.ctx.exit_flow()

    def _try_relocate(self, flow: Flow) -> str | None:
        """解析 relocate，返回跳转目标 id；None 表示不跳。

        fail 且无父级可上交时返回 ``Result.fail`` 语义：抛 JumpTargetError 不再合适，
        用 ``Result.fail`` 消息经由调用方——此处用特殊返回：raise 已改为返回
        并在入口处把「根上 fail」变成 fail Result。
        """
        if flow.relocate is None:
            return None
        outcome = resolve(flow.relocate, self.ctx)
        return self._outcome_to_target(flow, outcome)

    def _outcome_to_target(self, flow: Flow, outcome: Result | None) -> str | None:
        if outcome is None:
            return None
        if outcome.ok:
            return outcome.then
        # fail → 上交父级 / call 方
        parent_id = self.registry.parent_flow.get(flow.id)
        if parent_id is None:
            if self._call_stack and flow.id != self._call_stack[-1]:
                caller_id = self._call_stack[-1]
                logger.info("relocate fail → call 方 %s", caller_id)
                caller = self.registry.get(caller_id)
                assert isinstance(caller, Flow)
                return self._try_relocate(caller)
            raise _RelocateExhausted(outcome.message or "relocate 失败且无父级")
        parent = self.registry.get(parent_id)
        assert isinstance(parent, Flow)
        logger.info("relocate fail → 父级 %s", parent.id)
        return self._try_relocate(parent)

    def _leave_call_if_needed(self, flow: Flow, entry: str) -> None:
        """恢复目标不在当前 call 子树内时，ThenEscape 跳出 call。"""
        if not self._call_stack:
            return
        parent, _ = self.registry.entry_point(entry)
        if parent.id != flow.id:
            raise ThenEscape(entry)

    def _run_flow(self, flow: Flow) -> Result:
        logger.info("[%s]", flow.name)
        self.path.append(flow.id)
        self._flow_stack.append(flow.id)
        self.ctx.check_cancelled()
        self.ctx.enter_flow(flow.id, flow.params)
        try:
            try:
                entry = self._try_relocate(flow)
            except _RelocateExhausted as exc:
                return Result.fail(str(exc))
            if entry:
                self._leave_call_if_needed(flow, entry)
                parent, idx = self.registry.entry_point(entry)
                if parent.id == flow.id:
                    return self._run_flow_children(flow, idx)
                return self._run_subtree(entry)
            return self._run_flow_children(flow, 0)
        finally:
            self.ctx.exit_flow()
            self._flow_stack.pop()
            self.path.pop()

    def _run_flow_children(self, flow: Flow, start_index: int) -> Result:
        for i in range(start_index, len(flow.children)):
            self.ctx.check_cancelled()
            result = self._run_node(flow.children[i], parent_flow=flow, child_index=i)
            handled = self._consume_node_result(flow, i, result)
            if handled is not None:
                return handled
        return Result.success()

    def _consume_node_result(
        self, flow: Flow, child_index: int, result: Result | _FlowAdvance
    ) -> Result | None:
        if isinstance(result, _FlowAdvance):
            return self._run_flow_children(result.flow, result.start_index)
        if result.ok and result.then:
            handled = self._apply_then(result.then)
            if isinstance(handled, _FlowAdvance):
                return self._run_flow_children(handled.flow, handled.start_index)
            return handled
        if not result.ok:
            try:
                recovery = self._try_relocate(flow)
            except _RelocateExhausted:
                return result
            if recovery:
                self._leave_call_if_needed(flow, recovery)
                parent, idx = self.registry.entry_point(recovery)
                if parent.id == flow.id:
                    return self._run_flow_children(flow, idx)
                return self._run_subtree(recovery)
            return result
        return None

    def _apply_then(self, target_id: str) -> Result | _FlowAdvance:
        result = self._run_subtree(target_id)
        if not result.ok:
            return result
        if result.ok and result.then:
            return self._apply_then(result.then)
        return self._continue_after_node(target_id)

    def _run_node(
        self, node: Flow | Module, *, parent_flow: Flow, child_index: int
    ) -> Result | _FlowAdvance:
        if isinstance(node, Flow):
            return self._run_flow(node)

        logger.info("[%s]", node.name)
        self.path.append(node.id)
        self.ctx.check_cancelled()
        try:
            raw = node.active(self.ctx)
            outcome = normalize_outcome(raw)
            if outcome is None:
                outcome = Result.success()
        except ThenEscape as esc:
            self.path.pop()
            return self._apply_then(esc.target_id)
        except CancelledError:
            self.path.pop()
            return Result.fail("用户取消")
        self.path.pop()
        return outcome

    def _run_subtree(self, node_id: str) -> Result:
        node = self.registry.get(node_id)
        if isinstance(node, Module):
            logger.info("[%s]", node.name)
            self.path.append(node.id)
            self.ctx.check_cancelled()
            parent_id = self.registry.parent_flow[node_id]
            parent = self.registry.get(parent_id)
            assert isinstance(parent, Flow)
            if not self.ctx._params_stack:
                self.ctx.enter_flow(parent.id, parent.params)
                need_pop = True
            else:
                need_pop = False
            try:
                try:
                    raw = node.active(self.ctx)
                    outcome = normalize_outcome(raw)
                    if outcome is None:
                        outcome = Result.success()
                except ThenEscape as esc:
                    self.path.pop()
                    handled = self._apply_then(esc.target_id)
                    if isinstance(handled, _FlowAdvance):
                        return self._run_flow_children(handled.flow, handled.start_index)
                    return handled
                except CancelledError:
                    self.path.pop()
                    return Result.fail("用户取消")
                self.path.pop()
                if outcome.ok and outcome.then:
                    handled = self._apply_then(outcome.then)
                    if isinstance(handled, _FlowAdvance):
                        return self._run_flow_children(handled.flow, handled.start_index)
                    return handled
                return outcome
            finally:
                if need_pop:
                    self.ctx.exit_flow()
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


class _RelocateExhausted(Exception):
    """relocate 链走到根仍 fail。"""


def _prepare(
    flow: Flow,
    ctx: RunContext,
    config: RunConfig,
    *,
    root_id: str | None = None,
) -> Runner:
    from vision_bot.runtime.catalog import resolve_tool_flows

    reg = FlowRegistry.build(flow)
    for tool in resolve_tool_flows(root_id or flow.id, config.tools):
        reg.register_tool(tool)
    entry_id = config.entry_id or flow.id
    ctx._entry_flow_id = reg.flow_of(entry_id)
    ctx._run_param_overrides = dict(config.params)
    bind_runtime(ctx)
    runner = Runner(ctx, reg, root=flow)
    ctx._runner = runner
    return runner


def _run_loop(runner: Runner, ctx: RunContext, flow: Flow, config: RunConfig) -> RunReport:
    while not ctx.cancelled():
        if config.entry_id and config.entry_id != flow.id:
            result = runner.run_from(config.entry_id)
        else:
            result = runner.run_flow(flow)
        if not result.ok:
            if ctx.cancelled():
                return RunReport(success=False, message="用户取消", path=runner.path)
            return RunReport(success=False, message=result.message or "执行失败", path=runner.path)
        if not config.loop:
            return RunReport(success=True, message="完成", path=runner.path)
    return RunReport(success=False, message="用户取消", path=runner.path)


def run(
    flow: Flow,
    config: RunConfig,
    *,
    cancel_event=None,
    base_dir: Path | None = None,
    root_id: str | None = None,
) -> RunReport:
    bind_perception((base_dir or project_root()).resolve())
    ctx = RunContext(cancel_event=cancel_event)
    runner = _prepare(flow, ctx, config, root_id=root_id)
    return _run_loop(runner, ctx, flow, config)
