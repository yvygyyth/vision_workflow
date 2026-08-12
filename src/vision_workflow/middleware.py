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
    ModuleContext,
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
    module_ctx: ModuleContext | None = None


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
    """失败不立刻算真失败；耗尽 retries 次重试后才返回失败。

    触发重试的情况：
    - event 异常 / 返回非法 key（settled.ok=False）
    - 合法 key 且在 config['retry_on'] 中（默认空）
    """

    retries = max(0, int(retries))
    retry_delay_ms = max(0, int(retry_delay_ms))

    def mw(scope: ModuleScope, call_next: CallNext) -> Settled:
        label = scope.module.name or scope.module.id
        retry_on = {str(k) for k in (scope.module.config or {}).get("retry_on") or ()}
        last = Settled.reject("未执行")
        attempts = retries + 1
        for attempt in range(attempts):
            if scope.cancelled():
                return Settled.reject("用户取消", feedback="用户取消")
            last = call_next()
            key = scope.module_ctx.key if scope.module_ctx else None
            should_retry = (not last.ok) or (key is not None and key in retry_on)
            if not should_retry:
                return last
            if attempt + 1 >= attempts:
                break
            reason = last.feedback or last.error or (f"outcome={key}" if key else "")
            logger.info(
                "模块 [%s] 准备重试 %s/%s | %s",
                label,
                attempt + 1,
                retries,
                reason,
            )
            if retry_delay_ms > 0 and not scope.cancelled():
                scope.ctx.sleep(retry_delay_ms / 1000.0)
        return last

    return mw


def resolve_and_delay_middleware() -> ModuleMiddleware:
    """按 event 返回的 key 调用 on[key]，解析下一跳；继续时执行后延迟。"""

    def mw(scope: ModuleScope, call_next: CallNext) -> Settled:
        settled = call_next()
        mctx = scope.module_ctx
        mod = scope.module
        label = mod.name or mod.id

        # event 已校验 key；失败（异常 / 未知 key）直接结束本流程
        if not settled.ok or mctx is None or mctx.key is None:
            scope.next_id = END
            return settled

        key = mctx.key
        try:
            nxt = str(mod.on[key](mctx) or END)
        except Exception as exc:
            logger.exception("模块 on[%s] 异常 (%s)", key, mod.id)
            scope.next_id = END
            return Settled.reject(
                str(exc),
                value=mctx.value,
                feedback=f"({mod.id}) on[{key}] 异常",
            )

        scope.next_id = nxt

        if nxt == FAIL:
            settled = Settled.reject(
                f"outcome [{key}] → FAIL",
                value=mctx.value,
                feedback=f"({mod.id}) {key} → FAIL",
            )
        else:
            settled = Settled.resolve(
                mctx.value if mctx.value is not None else key,
                feedback=f"({mod.id}) {key} → {nxt}",
            )

        if settled.ok and nxt not in {END, FAIL, ""}:
            delay = resolve_delay_ms(scope.module.config, scope.workflow.module_delay_ms)
            if delay > 0 and not scope.cancelled():
                logger.info("延迟 %sms（模块后 %s）", delay, label)
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
    """核心：跑 event，校验返回值必须是 on 的某个 key。"""
    mod = scope.module
    label = mod.name or mod.id
    mctx = ModuleContext(
        ctx=scope.ctx,
        module=mod,
        flow=scope.flow,
        workflow=scope.workflow,
        cancelled=scope.cancelled,
    )
    scope.module_ctx = mctx

    logger.info("模块开始 (%s)", label)
    try:
        raw = mod.event(mctx)
    except Exception as exc:
        logger.exception("模块 event 异常 (%s)", mod.id)
        settled = Settled.reject(str(exc), feedback=f"({mod.id}) event 异常")
        logger.info("模块结束 (%s) ok=False", label)
        return settled

    mctx.key = str(raw)
    # 附带载荷由 event 写入 mctx.value

    if mctx.key not in mod.on:
        msg = f"未知结果 [{mctx.key}]，可选: {list(mod.on)}"
        logger.error("模块 [%s] %s", label, msg)
        settled = Settled.reject(msg, value=mctx.value, feedback=f"({mod.id}) {msg}")
        logger.info("模块结束 (%s) ok=False", label)
        return settled

    settled = Settled.resolve(
        mctx.value if mctx.value is not None else mctx.key,
        feedback=f"({mod.id}) outcome={mctx.key}",
    )
    logger.info("模块结束 (%s) key=%s", label, mctx.key)
    return settled


def execute_module(scope: ModuleScope) -> tuple[Settled, str]:
    """跑完洋葱栈，返回 (settled, next_module_id)。"""
    middlewares = build_module_middlewares(scope)
    settled = run_onion(scope, middlewares, lambda: run_module_event(scope))
    return settled, scope.next_id


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
        if settled.ok and nxt not in {END, FAIL, ""}:
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
