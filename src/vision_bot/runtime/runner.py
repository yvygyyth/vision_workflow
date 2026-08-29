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
from vision_bot.runtime.jump import Jump, JumpTargetError, Relocate, RelocateStop
from vision_bot.runtime.module import Module
from vision_bot.runtime.registry import FlowRegistry
from vision_bot.runtime.result import Result

logger = logging.getLogger(__name__)


@dataclass
class RunReport:
    success: bool
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
    def __init__(self, ctx: RunContext, registry: FlowRegistry, *, root: Flow) -> None:
        self.ctx = ctx
        self.registry = registry
        self.root = root
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
        except RelocateStop as exc:
            return Result.fail(str(exc))

    def run_from(self, entry_id: str) -> Result:
        node = self.registry.get(entry_id)
        if isinstance(node, Flow) and entry_id == self.root.id:
            return self.run_flow(node)
        parent, start_index = self.registry.entry_point(entry_id)
        self.ctx.enter_flow(parent.id, parent.params)
        try:
            return self._run_flow_children(parent, start_index)
        except RelocateStop as exc:
            return Result.fail(str(exc))
        except JumpTargetError as exc:
            return Result.fail(str(exc))
        finally:
            self.ctx.exit_flow()

    def _try_relocate(self, flow: Flow) -> str | None:
        from vision_bot.runtime.relocate import resolve

        # 未配置 relocate → 不跳转，由调用方从 children[0] 开跑
        if flow.relocate is None:
            return None
        target = resolve(flow.relocate, self.ctx)
        if target is Relocate.PARENT:
            parent_id = self.registry.parent_flow.get(flow.id)
            if parent_id is None:
                raise RelocateStop()
            parent = self.registry.get(parent_id)
            assert isinstance(parent, Flow)
            logger.info("relocate PARENT → %s", parent.id)
            return self._try_relocate(parent)
        if isinstance(target, str) and target:
            return target
        return None

    def _run_flow(self, flow: Flow) -> Result:
        logger.info("[%s]", flow.name)
        self.path.append(flow.id)
        self.ctx.check_cancelled()
        self.ctx.enter_flow(flow.id, flow.params)
        try:
            entry = self._try_relocate(flow)
            if entry:
                # 本 Flow 内的子节点：从该 index 起顺序执行后续兄弟
                parent, idx = self.registry.entry_point(entry)
                if parent.id == flow.id:
                    return self._run_flow_children(flow, idx)
                return self._run_subtree(entry)
            return self._run_flow_children(flow, 0)
        finally:
            self.ctx.exit_flow()
            self.path.pop()

    def _run_flow_children(self, flow: Flow, start_index: int) -> Result:
        for i in range(start_index, len(flow.children)):
            self.ctx.check_cancelled()
            result = self._run_node(flow.children[i], parent_flow=flow, child_index=i)
            handled = self._consume_node_result(flow, i, result)
            if handled is not None:
                return handled
        return Result.success()

    def _consume_node_result(self, flow: Flow, child_index: int, result: Result | _FlowAdvance) -> Result | None:
        if isinstance(result, _FlowAdvance):
            return self._run_flow_children(result.flow, result.start_index)
        if not result.ok:
            recovery = self._try_relocate(flow)
            if recovery:
                parent, idx = self.registry.entry_point(recovery)
                if parent.id == flow.id:
                    return self._run_flow_children(flow, idx)
                return self._run_subtree(recovery)
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
                    result = node.active(self.ctx)
                except Jump as jump:
                    self.path.pop()
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


def _prepare(
    flow: Flow,
    ctx: RunContext,
    config: RunConfig,
) -> Runner:
    reg = FlowRegistry.build(flow)
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
) -> RunReport:
    bind_perception((base_dir or project_root()).resolve())
    ctx = RunContext(cancel_event=cancel_event)
    runner = _prepare(flow, ctx, config)
    return _run_loop(runner, ctx, flow, config)
