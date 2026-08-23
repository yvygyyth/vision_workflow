"""Flow 执行器。"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from vision_bot.runtime.context import RunContext
from vision_bot.runtime.flow import Flow, StepFn, StepResult
from vision_bot.runtime.types import END, ESCALATE, FAIL, OK

logger = logging.getLogger(__name__)


@dataclass
class RunReport:
    success: bool
    outcome: str = ""
    message: str = ""
    path: list[str] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.path is None:
            self.path = []


def _try_relocate(flow: Flow, ctx: RunContext) -> str | None:
    if flow.relocate is None:
        return None
    detected = flow.relocate(ctx)
    if detected and detected in flow.steps:
        return detected
    return None


def _route_after_outcome(flow: Flow, current: str, outcome: str) -> tuple[str | None, bool]:
    """返回 (下一 step id, 是否结束本 Flow 并向上返回 outcome)。"""
    nxt = flow.on.get(outcome)
    if nxt is END:
        return None, True
    if isinstance(nxt, str):
        return nxt, False
    return None, True


def run_flow(flow: Flow, ctx: RunContext, *, parent: Flow | None = None) -> str:
    """执行嵌套 Flow；返回 outcome 或 ESCALATE。"""
    current = flow.entry

    while not ctx.cancelled():
        step = flow.get(current)
        logger.info("[%s] → %s", flow.id, current)

        if isinstance(step, Flow):
            outcome = run_flow(step, ctx, parent=flow)
            if outcome == ESCALATE:
                det = _try_relocate(flow, ctx)
                if det:
                    current = det
                    continue
                return ESCALATE
            nxt, done = _route_after_outcome(flow, current, outcome)
            if done:
                return outcome
            current = nxt  # type: ignore[assignment]
            continue

        assert isinstance(step, StepFn)
        result = step(ctx)

        if result.failed:
            routed = flow.resolve_route(current, result.outcome)
            if isinstance(routed, str):
                current = routed
                continue
            det = _try_relocate(flow, ctx)
            if det:
                current = det
                continue
            return ESCALATE

        if result.next_id is END:
            return result.outcome

        if result.next_id and isinstance(result.next_id, str):
            current = result.next_id
            continue

        routed = flow.resolve_route(current, result.outcome)
        if routed is END:
            return result.outcome
        if isinstance(routed, str):
            current = routed
            continue

        nxt = _default_next(flow, current)
        if nxt is None:
            return result.outcome if result.outcome != OK else OK
        current = nxt

    return FAIL


def run_root(flow: Flow, ctx: RunContext) -> RunReport:
    """顶层循环：子 Flow 结束后按 flow.on 路由；冒泡失败走 home_recovery。"""
    current = flow.entry
    path: list[str] = []

    while not ctx.cancelled():
        step = flow.get(current)
        path.append(f"{flow.id}.{current}")

        if isinstance(step, Flow):
            outcome = run_flow(step, ctx, parent=flow)
            if outcome == ESCALATE:
                det = _try_relocate(flow, ctx)
                if det:
                    current = det
                    continue
                if "home_recovery" in flow.steps:
                    logger.warning("顶层 relocate 失败 → home_recovery")
                    current = "home_recovery"
                    continue
                return RunReport(success=False, outcome=ESCALATE, message="无法识别界面", path=path)

            nxt, done = _route_after_outcome(flow, current, outcome)
            if not done and isinstance(nxt, str):
                current = nxt
                continue
            if done and flow.on.get(outcome) is END:
                return RunReport(success=True, outcome=outcome, path=path)
            hub = flow.on.get("back_to_hub")
            if isinstance(hub, str):
                current = hub
                continue
            return RunReport(success=True, outcome=outcome, path=path)

        assert isinstance(step, StepFn)
        result = step(ctx)
        if result.failed:
            routed = flow.resolve_route(current, result.outcome)
            if isinstance(routed, str):
                current = routed
                continue
            det = _try_relocate(flow, ctx)
            if det:
                current = det
                continue
            return RunReport(success=False, outcome=FAIL, message=result.message, path=path)

        if result.next_id is END:
            nxt = flow.on.get(result.outcome)
            if isinstance(nxt, str):
                current = nxt
                continue
            return RunReport(success=True, outcome=result.outcome, path=path)

        routed = flow.resolve_route(current, result.outcome)
        if isinstance(routed, str):
            current = routed
            continue

        nxt = _default_next(flow, current)
        if nxt:
            current = nxt
            continue
        return RunReport(success=True, outcome=result.outcome, path=path)

    return RunReport(success=False, outcome=FAIL, message="用户取消", path=path)


def _default_next(flow: Flow, step_id: str) -> str | None:
    ids = list(flow.steps.keys())
    try:
        idx = ids.index(step_id)
    except ValueError:
        return None
    if idx + 1 < len(ids):
        return ids[idx + 1]
    return None
