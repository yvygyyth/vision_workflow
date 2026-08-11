"""类 JS Promise 的流程链。

典型用法::

    P.find("email.png")
     .then(click_center)          # 事件（任意函数，不限于识图）
     .judge(P.exists("ok.png"))   # 判定函数 → 成功/失败
     .ok(on_success)              # 成功：下一步 / 再调某个方法
     .fail(on_fail)               # 失败：兜底
     .loop(3)                     # 整段失败时重试

    P.do(any_fn)                  # 完全不识图的一步
     .judge(check_fn)
     .ok(...)
     .fail(...)
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Self

from vision_workflow.models.flow import MatchResult

if TYPE_CHECKING:
    from vision_workflow.flow.context import FlowContext

logger = logging.getLogger(__name__)

Handler = Callable[["FlowContext", Any], Any]
JudgeFn = Callable[["FlowContext", Any], "bool | Settled | MatchResult"]


@dataclass
class Settled:
    """一次链结算结果（类似 Promise fulfilled / rejected）。"""

    ok: bool
    value: Any = None
    error: str = ""
    feedback: str = ""

    @classmethod
    def resolve(cls, value: Any = None, feedback: str = "") -> Settled:
        return cls(ok=True, value=value, feedback=feedback or "ok")

    @classmethod
    def reject(cls, error: str = "", value: Any = None, feedback: str = "") -> Settled:
        return cls(
            ok=False,
            value=value,
            error=error or "rejected",
            feedback=feedback or error or "failed",
        )


def _name(path: str) -> str:
    return Path(path).name


def _as_settled(result: Any, *, fallback_value: Any = None) -> Settled:
    if isinstance(result, Settled):
        return result
    if isinstance(result, MatchResult):
        if result.found:
            return Settled.resolve(result, feedback=f"识别到 [{_name(result.image)}]")
        return Settled.reject(
            result.message or "未识别到",
            value=result,
            feedback=f"未识别到 [{_name(result.image)}]",
        )
    if result is False:
        return Settled.reject("判定为 False", value=fallback_value)
    if result is None:
        return Settled.resolve(fallback_value)
    return Settled.resolve(result)


@dataclass
class _Node:
    kind: str
    fn: Handler | JudgeFn


@dataclass
class Promise:
    _starter: Handler | None = None
    _nodes: list[_Node] = field(default_factory=list)
    _loop_times: int = 1
    _loop_delay: float = 0.5
    name: str = ""

    @classmethod
    def do(cls, fn: Handler, *, name: str = "") -> Promise:
        return cls(_starter=fn, name=name or getattr(fn, "__name__", "do"))

    @classmethod
    def find(cls, image: str, **match_kwargs: Any) -> Promise:
        def _find(ctx: FlowContext, _value: Any = None) -> Settled:
            hit = ctx.find(image, **match_kwargs)
            if hit.found:
                return Settled.resolve(hit, feedback=f"识别到 [{_name(image)}]")
            return Settled.reject(
                hit.message or f"未找到 {image}",
                value=hit,
                feedback=f"未识别到 [{_name(image)}]",
            )

        return cls(_starter=_find, name=f"find:{_name(image)}")

    @classmethod
    def resolve(cls, value: Any = None) -> Promise:
        return cls(_starter=lambda ctx, _: Settled.resolve(value), name="resolve")

    @classmethod
    def reject(cls, error: str = "reject") -> Promise:
        return cls(_starter=lambda ctx, _: Settled.reject(error), name="reject")

    @staticmethod
    def exists(image: str, **match_kwargs: Any) -> JudgeFn:
        """判定函数：屏幕上是否出现某图。"""

        def _exists(ctx: FlowContext, _value: Any = None) -> Settled:
            kwargs = {"threshold": 0.8, "timeout": 5.0, **match_kwargs}
            hit = ctx.find(image, **kwargs)
            if hit.found:
                return Settled.resolve(hit, feedback=f"确认出现 [{_name(image)}]")
            return Settled.reject(
                hit.message or f"未确认到 {image}",
                value=hit,
                feedback=f"未确认到 [{_name(image)}]",
            )

        return _exists

    def then(self, fn: Handler) -> Self:
        self._nodes.append(_Node("then", fn))
        return self

    def catch(self, fn: Handler) -> Self:
        self._nodes.append(_Node("catch", fn))
        return self

    def judge(self, fn: JudgeFn) -> Self:
        """事件之后的判定函数：成功/失败分流。"""
        self._nodes.append(_Node("judge", fn))
        return self

    def ok(self, fn: Handler) -> Self:
        self._nodes.append(_Node("ok", fn))
        return self

    def fail(self, fn: Handler) -> Self:
        self._nodes.append(_Node("fail", fn))
        return self

    def loop(self, times: int = 3, delay: float = 0.5) -> Self:
        """失败时重试整条链。"""
        self._loop_times = max(1, int(times))
        self._loop_delay = max(0.0, float(delay))
        return self

    def run(self, ctx: FlowContext) -> Settled:
        last = Settled.reject("empty promise")
        for attempt in range(1, self._loop_times + 1):
            last = self._run_once(ctx)
            if last.ok:
                return last
            if attempt < self._loop_times:
                logger.info(
                    "Promise[%s] %s/%s 失败，%.2fs 后重试 | %s",
                    self.name or "anon",
                    attempt,
                    self._loop_times,
                    self._loop_delay,
                    last.feedback or last.error,
                )
                ctx.sleep(self._loop_delay)
        return last

    def _run_once(self, ctx: FlowContext) -> Settled:
        state = Settled.resolve(None)
        if self._starter is not None:
            state = self._invoke(ctx, self._starter, state.value, as_judge=False)

        for node in self._nodes:
            if node.kind in {"then", "ok"} and state.ok:
                state = self._invoke(ctx, node.fn, state.value, as_judge=False)
            elif node.kind in {"catch", "fail"} and not state.ok:
                state = self._invoke(ctx, node.fn, state.value, as_judge=False)
            elif node.kind == "judge" and state.ok:
                state = self._invoke(ctx, node.fn, state.value, as_judge=True)
        return state

    def _invoke(
        self,
        ctx: FlowContext,
        fn: Handler | JudgeFn,
        value: Any,
        *,
        as_judge: bool,
    ) -> Settled:
        try:
            out = fn(ctx, value)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Promise handler 异常: %s", exc)
            return Settled.reject(str(exc), value=value)

        if isinstance(out, Promise):
            return out.run(ctx)

        if as_judge:
            if isinstance(out, bool):
                return (
                    Settled.resolve(value, feedback="判定成功")
                    if out
                    else Settled.reject("判定失败", value=value, feedback="判定失败")
                )
            return _as_settled(out, fallback_value=value)

        if out is None:
            return Settled.resolve(value)
        return _as_settled(out, fallback_value=value)


P = Promise
