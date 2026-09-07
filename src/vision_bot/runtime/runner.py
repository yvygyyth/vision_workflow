"""流程执行器（trampoline：return / goto / call，不靠递归嵌套）。

静态树只决定默认兄弟顺跑；运行真相是 ``_flow_stack``。
``Result.then`` / 返回字符串 = return（栈内 Flow 或同父兄弟）。
``ctx.goto`` = 全开跳转；真栈外裁到入口再 dispatch，不重建中间 Flow。
失败与入口 relocate 沿运行栈上冒，按 flow_id 去重。
relocate 跳到 Flow 外时仍用一次性 ``_resume_after``，避免目标顺延回原 Flow。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import NoReturn

from vision_bot.core.paths import project_root
from vision_bot.perception.session import bind_perception
from vision_bot.runtime.bind import bind_runtime
from vision_bot.runtime.cancel import CancelledError
from vision_bot.runtime.config import RunConfig
from vision_bot.runtime.context import RunContext
from vision_bot.runtime.flow import Flow
from vision_bot.runtime.jump import JumpEscape, JumpTargetError
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
    """relocate 沿栈走到入口仍 fail。"""


class Runner:
    def __init__(self, ctx: RunContext, registry: FlowRegistry, *, root: Flow) -> None:
        self.ctx = ctx
        self.registry = registry
        self.root = root
        self.path: list[str] = []
        self._flow_stack: list[str] = []
        # 每层 drive 不允许「正常结束」时 pop 到该深度以下（call 挡住调用方）
        self._drive_floors: list[int] = []
        # 本轮失败/入口 relocate 已尝试过的 flow_id
        self._relocate_tried: set[str] = set()
        # relocate 跳到外部后，目标跑完续跑「发起方 Flow」之后的兄弟（goto/return 会清除）
        self._resume_after: str | None = None
        # 真栈外 goto 裁剪锚点（通常为根）
        self._entry_flow_id: str = root.id

    def call(self, target_id: str) -> Result:
        """同步插入执行；内部 goto 逃出时抛 ``JumpEscape``，不回到调用点。"""
        if not self._flow_stack:
            raise RuntimeError("call 必须在 Flow 执行中调用")
        self.registry.get(target_id)
        depth = len(self._flow_stack)
        try:
            return self._drive(target_id)
        finally:
            while len(self._flow_stack) > depth:
                self._pop_flow()

    def goto(self, target_id: str) -> NoReturn:
        """无限制跳转；通过 ``JumpEscape`` 交给 trampoline。"""
        self.registry.get(target_id)
        self._resume_after = None
        self._trim_for_goto(target_id)
        raise JumpEscape(target_id)

    def run_flow(self, flow: Flow) -> Result:
        self._entry_flow_id = flow.id
        return self._run_top(flow.id)

    def run_from(self, entry_id: str) -> Result:
        """从 ``entry_id`` 启动：等价于以根为入口后 ``goto`` 到目标。

        压入 ``root → … → 目标祖先``（不跑中间 relocate），目标跑完后
        继续父级后续兄弟，并向上回到根。
        """
        self.registry.get(entry_id)
        if entry_id == self.root.id:
            return self.run_flow(self.root)

        # 栈外 goto 锚在根；params 覆盖仍用 ctx._entry_flow_id（入口所属 Flow）
        self._entry_flow_id = self.root.id
        for fid in self._ancestor_chain(entry_id)[:-1]:
            ancestor = self.registry.get(fid)
            if isinstance(ancestor, Flow):
                self._push_flow(ancestor)
        try:
            return self._run_top(entry_id, drive_floor=0)
        finally:
            while self._flow_stack:
                self._pop_flow()

    def _run_top(self, start_id: str, *, drive_floor: int | None = None) -> Result:
        try:
            return self._drive(start_id, drive_floor=drive_floor)
        except JumpTargetError as exc:
            return Result.fail(str(exc))
        except JumpEscape as esc:
            try:
                return self._drive(esc.target_id, drive_floor=drive_floor)
            except JumpTargetError as exc:
                return Result.fail(str(exc))

    def _drive(self, start_id: str, *, drive_floor: int | None = None) -> Result:
        """调度循环。

        ``drive_floor`` 默认取进入时栈深（call 挡住调用方）；
        ``run_from`` 传 ``0``，使目标结束后仍能回到根并继续兄弟。
        """
        self._drive_floors.append(
            len(self._flow_stack) if drive_floor is None else drive_floor
        )
        try:
            pend: str | None = start_id
            while pend is not None:
                self.ctx.check_cancelled()
                try:
                    out = self._step(pend)
                except JumpEscape as esc:
                    if self._escaped_current_drive():
                        raise
                    pend = esc.target_id
                    continue
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

    def _escaped_current_drive(self) -> bool:
        """嵌套 drive（call）中栈已回到起点及以下 → 应交给外层 trampoline。"""
        return len(self._drive_floors) > 1 and len(self._flow_stack) <= self._drive_floor()

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
            entry = self._try_relocate_along_stack(
                from_flow_id=flow.id,
                allow_skip_unconfigured=True,
            )
        except _RelocateExhausted as exc:
            self._pop_flow()
            return Result.fail(str(exc))
        if entry:
            # 目标是本 Flow 直接子节点：顺延；否则续跑本 Flow 之后
            if self.registry.parent_flow.get(entry) == flow.id:
                self._resume_after = None
            else:
                self._resume_after = flow.id
            return self._pend_jump(entry)
        if not flow.children:
            return self._finish_flow()
        return flow.children[0].id

    def _step_mod(self, node: Module) -> str | Result | None:
        parent_id = self.registry.parent_flow.get(node.id)
        if parent_id and parent_id not in self._flow_stack:
            parent = self.registry.get(parent_id)
            assert isinstance(parent, Flow)
            # 不跑入口 relocate，只保证父帧在栈上以便 _after / params
            self._push_flow(parent)
        logger.info("[%s]", node.name)
        self.path.append(node.id)
        self.ctx.check_cancelled()
        try:
            outcome = normalize_outcome(node.active(self.ctx))
            if outcome is None:
                outcome = Result.success()
        except JumpEscape as esc:
            self.path.pop()
            if self._escaped_current_drive():
                raise
            return esc.target_id
        except CancelledError:
            self.path.pop()
            return Result.fail("用户取消")
        self.path.pop()

        if not outcome.ok:
            return self._recover(node, outcome)
        if outcome.then:
            self._resume_after = None
            self._ensure_return_allowed(from_mod_id=node.id, target_id=outcome.then)
            return self._pend_jump(outcome.then)
        return self._continue(node.id)

    def _recover(self, node: Module, fail: Result) -> str | Result | None:
        parent_id = self.registry.parent_flow[node.id]
        try:
            recovery = self._try_relocate_along_stack(
                from_flow_id=parent_id,
                allow_skip_unconfigured=False,
            )
        except _RelocateExhausted:
            return fail
        if not recovery:
            return fail
        self._resume_after = parent_id
        return self._pend_jump(recovery)

    def _pend_jump(self, target_id: str) -> str:
        """裁栈后交给 trampoline；若已逃出当前 drive 则抛 ``JumpEscape``。"""
        self._trim_for_goto(target_id)
        if self._escaped_current_drive():
            raise JumpEscape(target_id)
        return target_id

    def _continue(self, node_id: str) -> str | Result | None:
        origin = self._take_resume_after()
        return self._after(origin if origin is not None else node_id)

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
        origin = self._take_resume_after()
        if origin is not None:
            return self._after(origin)
        if len(self._flow_stack) <= self._drive_floor():
            return None
        return self._after(finished_id)

    def _take_resume_after(self) -> str | None:
        origin = self._resume_after
        self._resume_after = None
        return origin

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

    def _ensure_return_allowed(self, *, from_mod_id: str, target_id: str) -> None:
        """return 语义：仅栈内 Flow 或同父兄弟。"""
        self.registry.get(target_id)
        if target_id in self._flow_stack:
            return
        from_parent = self.registry.parent_flow.get(from_mod_id)
        target_parent = self.registry.parent_flow.get(target_id)
        if from_parent is not None and from_parent == target_parent:
            return
        raise JumpTargetError(
            f"return 越界: {from_mod_id!r} → {target_id!r}"
            f"（仅允许栈内 Flow 或同父兄弟；更大跳转请用 ctx.goto）"
        )

    def _trim_for_goto(self, target_id: str) -> None:
        """按 goto 规则裁剪栈（不重建中间帧）。"""
        if target_id in self._flow_stack:
            while self._flow_stack and self._flow_stack[-1] != target_id:
                self._pop_flow()
            return

        ancestor = self._nearest_stack_ancestor(target_id)
        if ancestor is not None:
            while self._flow_stack and self._flow_stack[-1] != ancestor:
                self._pop_flow()
            return

        # 真栈外：裁到入口 Flow（若入口不在栈上则清空后推入口）
        entry = self._entry_flow_id
        while self._flow_stack and self._flow_stack[-1] != entry:
            self._pop_flow()
        if not self._flow_stack:
            entry_node = self.registry.get(entry)
            if isinstance(entry_node, Flow):
                self._push_flow(entry_node)
            else:
                parent_id = self.registry.parent_flow[entry]
                parent = self.registry.get(parent_id)
                assert isinstance(parent, Flow)
                self._push_flow(parent)

    def _nearest_stack_ancestor(self, node_id: str) -> str | None:
        cur: str | None = node_id
        while cur is not None:
            if cur in self._flow_stack:
                return cur
            cur = self.registry.parent_flow.get(cur)
        return None

    def _ancestor_chain(self, node_id: str) -> list[str]:
        """``root → … → node_id``（含自身）。"""
        chain: list[str] = []
        cur: str | None = node_id
        while cur is not None:
            chain.append(cur)
            cur = self.registry.parent_flow.get(cur)
        chain.reverse()
        return chain

    def _try_relocate_along_stack(
        self,
        *,
        from_flow_id: str,
        allow_skip_unconfigured: bool,
    ) -> str | None:
        """从 from_flow_id 起沿运行栈向上 relocate；成功返回目标 id。

        ``allow_skip_unconfigured=True``（入口）：起始 Flow 未配置 relocate 则直接
        不跳转（children[0]），不上冒。
        ``False``（失败恢复）：无 relocate 的帧跳过，继续向上找。
        """
        start = self.registry.get(from_flow_id)
        if (
            allow_skip_unconfigured
            and isinstance(start, Flow)
            and start.relocate is None
        ):
            return None

        if from_flow_id not in self._flow_stack:
            chain = [from_flow_id]
        else:
            idx = self._flow_stack.index(from_flow_id)
            chain = list(reversed(self._flow_stack[: idx + 1]))

        last_fail: Result | None = None
        saw_configured = False
        for flow_id in chain:
            if flow_id in self._relocate_tried:
                continue
            node = self.registry.get(flow_id)
            if not isinstance(node, Flow) or node.relocate is None:
                continue
            saw_configured = True
            self._relocate_tried.add(flow_id)
            outcome = resolve(node.relocate, self.ctx)
            if outcome is None:
                self._relocate_tried.clear()
                return None
            if outcome.ok:
                self._relocate_tried.clear()
                return outcome.then
            last_fail = outcome
            logger.info("relocate fail @ %s → 继续上冒", flow_id)

        self._relocate_tried.clear()
        if not saw_configured and allow_skip_unconfigured:
            return None
        msg = (last_fail.message if last_fail else None) or "relocate 失败且已到入口"
        raise _RelocateExhausted(msg)


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
    runner._entry_flow_id = ctx._entry_flow_id
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
