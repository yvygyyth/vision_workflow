"""洋葱中间件：重试 / 延迟等横切能力叠在核心事件外。

执行顺序（由外到内）::

    Resolve+Delay → Retry → Event

进入时先入外层；返回时先出内层。新增能力只需加中间件，不必改 Runner 主循环。
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Protocol

from vision_workflow.flow.context import FlowContext
from vision_workflow.module import (
    END,
    FAIL,
    Flow,
    Module,
    Workflow,
    resolve_delay_ms,
    resolve_next,
)
from vision_workflow.promise import Settled

logger = logging.getLogger(__name__)

CallNext = Callable[[], Settled]


@dataclass
class ModuleScope:
    ctx: FlowContext
    module: Module
    flow: Flow
    workflow: Workflow
    cancelled: Callable[[], bool] = field(default=lambda: False)
    next_id: str = END


class ModuleMiddleware(Protocol):
    def __call__(self, scope: ModuleScope, call_next: CallNext) -> Settled: ...


def run_onion(scope: ModuleScope, middlewares: list[ModuleMiddleware], core: CallNext) -> Settled:
    """middlewares[0] 为最外层。"""

    def bind(index: int) -> CallNext:
        if index >= len(middlewares):
            return core

        mw = middlewares[index]

        def _wrapped() -> Settled:
            return mw(scope, bind(index + 1))

        return _wrapped

    return bind(0)()


def retry_middleware(*, retries: int, retry_delay_ms: int = 0) -> ModuleMiddleware:
    """失败不立刻算真失败；耗尽 retries 次重试后才返回失败。"""

    retries = max(0, int(retries))
    retry_delay_ms = max(0, int(retry_delay_ms))

    def mw(scope: ModuleScope, call_next: CallNext) -> Settled:
        label = scope.module.name or scope.module.id
        last = Settled.reject("未执行")
        attempts = retries + 1
        for attempt in range(attempts):
            if scope.cancelled():
                return Settled.reject("用户取消", feedback="用户取消")
            last = call_next()
            if last.ok:
                return last
            if attempt + 1 >= attempts:
                break
            logger.info(
                "模块 [%s] 失败，准备重试 %s/%s | %s",
                label,
                attempt + 1,
                retries,
                last.feedback or last.error,
            )
            if retry_delay_ms > 0 and not scope.cancelled():
                scope.ctx.sleep(retry_delay_ms / 1000.0)
        return last

    return mw


def resolve_and_delay_middleware() -> ModuleMiddleware:
    """解析下一跳；若成功且还将继续下一模块，则执行后延迟。"""

    def mw(scope: ModuleScope, call_next: CallNext) -> Settled:
        settled = call_next()
        default_success = scope.flow.default_success_for(scope.module.id)
        if settled.ok:
            nxt = resolve_next(
                scope.module.success,
                scope.ctx,
                settled.value,
                default=default_success,
            )
        else:
            nxt = resolve_next(scope.module.fail, scope.ctx, settled.value, default=END)
        scope.next_id = nxt

        if settled.ok and nxt not in {END, FAIL, None, ""}:
            delay = resolve_delay_ms(scope.module.config, scope.workflow.module_delay_ms)
            if delay > 0 and not scope.cancelled():
                logger.info("延迟 %sms（模块后 %s）", delay, scope.module.name or scope.module.id)
                scope.ctx.sleep(delay / 1000.0)
        return settled

    return mw


def build_module_middlewares(scope: ModuleScope) -> list[ModuleMiddleware]:
    """按 config 组装洋葱（列表首元素 = 最外层）。"""
    cfg = scope.module.config or {}
    retries = int(cfg.get("retry", 0) or 0)
    retry_delay_ms = int(cfg.get("retry_delay_ms", 0) or 0)

    # 外 → 内：先解析/延迟，再重试，再事件
    stack: list[ModuleMiddleware] = [resolve_and_delay_middleware()]
    if retries > 0:
        stack.append(retry_middleware(retries=retries, retry_delay_ms=retry_delay_ms))
    return stack


def run_module_event(scope: ModuleScope) -> Settled:
    """核心：只跑 event，不解析跳转。"""
    mod = scope.module
    label = mod.name or mod.id
    logger.info("模块开始 (%s)", label)
    try:
        raw = mod.event(scope.ctx)
    except Exception as exc:  # noqa: BLE001
        logger.exception("模块 event 异常 (%s): %s", mod.id, exc)
        settled = Settled.reject(str(exc), feedback=f"({mod.id}) event 异常")
        logger.info("模块结束 (%s) ok=False", label)
        return settled

    if isinstance(raw, Settled):
        settled = raw
    else:
        settled = Settled.resolve(raw)
    logger.info("模块结束 (%s) ok=%s", label, settled.ok)
    return settled


def execute_module(scope: ModuleScope) -> tuple[Settled, str]:
    """跑完洋葱栈，返回 (settled, next_module_id)。"""
    middlewares = build_module_middlewares(scope)
    settled = run_onion(scope, middlewares, lambda: run_module_event(scope))
    nxt = scope.next_id
    settled.feedback = settled.feedback or (
        f"({scope.module.id}) 成功 → {nxt}" if settled.ok else f"({scope.module.id}) 失败 → {nxt}"
    )
    return settled, nxt


# ----- Flow 级洋葱（流程重试 / 流程后延迟）-----


@dataclass
class FlowScope:
    ctx: FlowContext
    flow: Flow
    workflow: Workflow
    cancelled: Callable[[], bool] = field(default=lambda: False)
    next_flow_id: str = END
    last_settled: Settled | None = None


CallNextFlow = Callable[[], Settled]


class FlowMiddleware(Protocol):
    def __call__(self, scope: FlowScope, call_next: CallNextFlow) -> Settled: ...


def run_flow_onion(
    scope: FlowScope,
    middlewares: list[FlowMiddleware],
    core: CallNextFlow,
) -> Settled:
    def bind(index: int) -> CallNextFlow:
        if index >= len(middlewares):
            return core
        mw = middlewares[index]

        def _wrapped() -> Settled:
            return mw(scope, bind(index + 1))

        return _wrapped

    return bind(0)()


def flow_retry_middleware(*, retries: int, retry_delay_ms: int = 0) -> FlowMiddleware:
    retries = max(0, int(retries))
    retry_delay_ms = max(0, int(retry_delay_ms))

    def mw(scope: FlowScope, call_next: CallNextFlow) -> Settled:
        last = Settled.reject("未执行")
        attempts = retries + 1
        for attempt in range(attempts):
            if scope.cancelled():
                return Settled.reject("用户取消", feedback="用户取消")
            last = call_next()
            if last.ok:
                return last
            if attempt + 1 >= attempts:
                break
            logger.info(
                "流程 [%s] 失败，准备重试 %s/%s | %s",
                scope.flow.display_name,
                attempt + 1,
                retries,
                last.feedback or last.error,
            )
            if retry_delay_ms > 0 and not scope.cancelled():
                scope.ctx.sleep(retry_delay_ms / 1000.0)
        return last

    return mw


def flow_resolve_and_delay_middleware() -> FlowMiddleware:
    def mw(scope: FlowScope, call_next: CallNextFlow) -> Settled:
        settled = call_next()
        scope.last_settled = settled
        if settled.ok:
            nxt = resolve_next(scope.flow.success, scope.ctx, settled.value, default=END)
        else:
            nxt = resolve_next(scope.flow.fail, scope.ctx, settled.value, default=END)
        scope.next_flow_id = nxt
        if settled.ok and nxt not in {END, FAIL, None, ""}:
            delay = resolve_delay_ms(scope.flow.config, scope.workflow.flow_delay_ms)
            if delay > 0 and not scope.cancelled():
                logger.info("延迟 %sms（流程后 %s）", delay, scope.flow.display_name)
                scope.ctx.sleep(delay / 1000.0)
        return settled

    return mw


def build_flow_middlewares(scope: FlowScope) -> list[FlowMiddleware]:
    cfg = scope.flow.config or {}
    retries = int(cfg.get("retry", 0) or 0)
    retry_delay_ms = int(cfg.get("retry_delay_ms", 0) or 0)
    stack: list[FlowMiddleware] = [flow_resolve_and_delay_middleware()]
    if retries > 0:
        stack.append(flow_retry_middleware(retries=retries, retry_delay_ms=retry_delay_ms))
    return stack
