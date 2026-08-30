"""流程执行器（trampoline：then / 续跑不递归嵌套）。

对象树只决定「默认顺跑兄弟」；每个 Flow 都可独立进入。
``call`` 开启嵌套 drive，用 floor 挡住调用方栈，与是否 register_tool 无关。
"""

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


class _RelocateExhausted(Exception):
    """relocate 链走到根仍 fail。"""


class Runner:
    def __init__(self, ctx: RunContext, registry: FlowRegistry, *, root: Flow) -> None:
        self.ctx = ctx
        self.registry = registry
        self.root = root
        self.path: list[str] = []
        self._flow_stack: list[str] = []
        self._call_stack: list[str] = []
        # 每层 drive 不允许 pop 到该深度以下（call 嵌套时挡住调用方）
        self._drive_floors: list[int] = []
        # relocate 跳到外部后，目标结束应续跑「发起方 Flow」之后的兄弟
        self._resume_after: str | None = None

    def call(self, target_id: str) -> Result:
        """同步插入执行任意 Flow/节点；子树外跳转抛 ``ThenEscape``。"""
        if not self._flow_stack:
            raise RuntimeError("call 必须在 Flow 执行中调用")
        self.registry.get(target_id)
        self._call_stack.append(self._flow_stack[-1])
        depth = len(self._flow_stack)
        try:
            return self._drive(target_id)
        finally:
            while len(self._flow_stack) > depth:
                self._pop_flow()
            self._call_stack.pop()

    def run_flow(self, flow: Flow) -> Result:
        try:
            return self._drive(flow.id)
        except JumpTargetError as exc:
            return Result.fail(str(exc))

    def run_from(self, entry_id: str) -> Result:
        node = self.registry.get(entry_id)
        if isinstance(node, Flow) and entry_id == self.root.id:
            return self.run_flow(node)
        parent, start_index = self.registry.entry_point(entry_id)
        self._push_flow(parent)
        try:
            return self._drive(parent.children[start_index].id)
        except JumpTargetError as exc:
            return Result.fail(str(exc))
        finally:
            while self._flow_stack:
                self._pop_flow()

    def _drive(self, start_id: str) -> Result:
        """调度循环。floor = 进入本 drive 时的栈深；回到该深度即本 drive 结束。"""
        self._drive_floors.append(len(self._flow_stack))
        try:
            pend: str | None = start_id
            while pend is not None:
                self.ctx.check_cancelled()
                out = self._step(pend)
                if out is None:
                    return Result.success()
                if isinstance(out, Result):
                    return out
                pend = out
            return Result.success()
        finally:
            self._drive_floors.pop()

    def _drive_floor(self) -> int:
        return self._drive_floors[-1] if self._drive_floors else 0

    def _step(self, target_id: str) -> str | Result | None:
        node = self.registry.get(target_id)
        if isinstance(node, Flow):
            return self._step_flow(node)
        return self._step_mod(node)

    def _step_flow(self, flow: Flow) -> str | Result | None:
        if not (self._flow_stack and self._flow_stack[-1] == flow.id):
            self._push_flow(flow)
        return self._dispatch_flow(flow)

    def _dispatch_flow(self, flow: Flow) -> str | Result | None:
        try:
            entry = self._try_relocate(flow)
        except _RelocateExhausted as exc:
            self._pop_flow()
            return Result.fail(str(exc))
        if entry:
            self._leave_call_if_needed(flow, entry)
            parent, idx = self.registry.entry_point(entry)
            if parent.id == flow.id:
                self._resume_after = None
                return parent.children[idx].id
            self._resume_after = flow.id
            self._unwind_for(entry)
            return entry
        if not flow.children:
            return self._finish_flow()
        return flow.children[0].id

    def _step_mod(self, node: Module) -> str | Result | None:
        logger.info("[%s]", node.name)
        self.path.append(node.id)
        self.ctx.check_cancelled()
        try:
            outcome = normalize_outcome(node.active(self.ctx))
            if outcome is None:
                outcome = Result.success()
        except ThenEscape as esc:
            self.path.pop()
            self._resume_after = None
            self._unwind_for(esc.target_id)
            return esc.target_id
        except CancelledError:
            self.path.pop()
            return Result.fail("用户取消")
        self.path.pop()

        if not outcome.ok:
            return self._recover(node, outcome)
        if outcome.then:
            self._leave_call_if_needed_from_mod(node, outcome.then)
            self._resume_after = None
            self._unwind_for(outcome.then)
            return outcome.then
        return self._continue(node.id)

    def _recover(self, node: Module, fail: Result) -> str | Result | None:
        parent_id = self.registry.parent_flow[node.id]
        parent = self.registry.get(parent_id)
        assert isinstance(parent, Flow)
        try:
            recovery = self._try_relocate(parent)
        except _RelocateExhausted:
            return fail
        if not recovery:
            return fail
        self._leave_call_if_needed(parent, recovery)
        self._resume_after = parent.id
        self._unwind_for(recovery)
        return recovery

    def _continue(self, node_id: str) -> str | Result | None:
        if self._resume_after is not None:
            origin = self._resume_after
            self._resume_after = None
            return self._after(origin)
        return self._after(node_id)

    def _after(self, node_id: str) -> str | Result | None:
        nxt = self.registry.next_sibling_index(node_id)
        if nxt is not None:
            parent_id, index = nxt
            parent = self.registry.get(parent_id)
            assert isinstance(parent, Flow)
            return parent.children[index].id
        return self._finish_flow()

    def _finish_flow(self) -> str | Result | None:
        if not self._flow_stack:
            return None
        finished_id = self._flow_stack[-1]
        self._pop_flow()
        if self._resume_after is not None:
            origin = self._resume_after
            self._resume_after = None
            return self._after(origin)
        # 回到本 drive 的 floor：独立 Flow（含 call 目标）结束，不再 pop 外层
        if len(self._flow_stack) <= self._drive_floor():
            return None
        return self._after(finished_id)

    def _push_flow(self, flow: Flow) -> None:
        logger.info("[%s]", flow.name)
        self.path.append(flow.id)
        self._flow_stack.append(flow.id)
        self.ctx.enter_flow(flow.id, flow.params)

    def _pop_flow(self) -> None:
        if not self._flow_stack:
            return
        self.ctx.exit_flow()
        self._flow_stack.pop()
        if self.path:
            self.path.pop()

    def _unwind_for(self, target_id: str) -> None:
        """弹出非祖先 Frame，避免 then/relocate 叠在旁路 Flow 上。"""
        floor = self._drive_floor()
        target_flow = self.registry.flow_of(target_id)
        while len(self._flow_stack) > floor:
            top = self._flow_stack[-1]
            if top == target_flow or self._is_under(target_id, ancestor=top):
                return
            self._pop_flow()

    def _is_under(self, node_id: str, *, ancestor: str) -> bool:
        cur: str | None = node_id
        while cur is not None:
            if cur == ancestor:
                return True
            cur = self.registry.parent_flow.get(cur)
        return False

    def _try_relocate(self, flow: Flow) -> str | None:
        if flow.relocate is None:
            return None
        return self._outcome_to_target(flow, resolve(flow.relocate, self.ctx))

    def _outcome_to_target(self, flow: Flow, outcome: Result | None) -> str | None:
        if outcome is None:
            return None
        if outcome.ok:
            return outcome.then
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
        if not self._call_stack:
            return
        parent, _ = self.registry.entry_point(entry)
        if parent.id != flow.id:
            raise ThenEscape(entry)

    def _leave_call_if_needed_from_mod(self, node: Module, entry: str) -> None:
        if not self._call_stack:
            return
        parent_id = self.registry.parent_flow[node.id]
        parent = self.registry.get(parent_id)
        assert isinstance(parent, Flow)
        self._leave_call_if_needed(parent, entry)


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
