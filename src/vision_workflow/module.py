"""组合式平级模块：每个模块是完整小生命周期，靠 id 互相跳转。

生命周期::

    action(ctx) → judge(ctx, value) → success/fail 指定下一个模块 id

跳转目标可以是：
- 其它模块 id
- END / FAIL
- 函数 (ctx, value) -> 下一个 id
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from vision_workflow.flow.context import FlowContext
from vision_workflow.promise import Settled

logger = logging.getLogger(__name__)

END = "end"
FAIL = "fail"

# action: 只接收 ctx，返回任意值 / Settled
ActionFn = Callable[[FlowContext], Any]
# judge: 判定成功与否
JudgeFn = Callable[[FlowContext, Any], bool | Settled]
# 下一跳：写死 id，或动态计算
NextRef = str | Callable[[FlowContext, Any], str] | None


@dataclass
class Module:
    """一个平级的完整小流程。"""

    id: str
    action: ActionFn
    judge: JudgeFn | None = None
    success: NextRef = END
    fail: NextRef = FAIL
    name: str = ""
    enabled: bool = True
    max_loops: int = 0  # 本模块被跳回时的最大执行次数，0=不限制（仍受全局 guard 保护）

    def lifecycle(self, ctx: FlowContext) -> tuple[Settled, str]:
        """执行一轮生命周期，返回 (结果, 下一个模块id)。"""
        label = self.name or self.id
        logger.info("模块开始 (%s)", label)

        try:
            raw = self.action(ctx)
        except Exception as exc:  # noqa: BLE001
            logger.exception("模块 action 异常 (%s): %s", self.id, exc)
            settled = Settled.reject(str(exc), feedback=f"({self.id}) action 异常")
            return settled, self._resolve_next(self.fail, ctx, None)

        if isinstance(raw, Settled):
            settled = raw
            value = raw.value
        else:
            value = raw
            settled = Settled.resolve(value)

        # 判定阶段（可选）
        if settled.ok and self.judge is not None:
            try:
                judged = self.judge(ctx, value)
            except Exception as exc:  # noqa: BLE001
                logger.exception("模块 judge 异常 (%s): %s", self.id, exc)
                settled = Settled.reject(str(exc), value=value, feedback=f"({self.id}) judge 异常")
            else:
                if isinstance(judged, Settled):
                    settled = judged
                elif judged:
                    settled = Settled.resolve(
                        value,
                        feedback=settled.feedback or f"({self.id}) 判定成功",
                    )
                else:
                    settled = Settled.reject(
                        "判定失败",
                        value=value,
                        feedback=f"({self.id}) 判定失败",
                    )

        nxt = self._resolve_next(self.success if settled.ok else self.fail, ctx, settled.value)
        settled.feedback = settled.feedback or (
            f"({self.id}) 成功 → {nxt}" if settled.ok else f"({self.id}) 失败 → {nxt}"
        )
        logger.info("模块结束 (%s) ok=%s → %s", label, settled.ok, nxt)
        return settled, nxt

    def _resolve_next(self, ref: NextRef, ctx: FlowContext, value: Any) -> str:
        if ref is None:
            return END
        if callable(ref):
            return str(ref(ctx, value) or END)
        return str(ref)


@dataclass
class ModuleGraph:
    """平级模块集合，按 id 跳转执行。"""

    modules: list[Module]
    entry: str
    name: str = "flow"
    dry_run: bool = False
    base_dir: str | None = None

    _by_id: dict[str, Module] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        ids = [m.id for m in self.modules]
        if len(ids) != len(set(ids)):
            raise ValueError(f"模块 id 必须唯一: {ids}")
        self._by_id = {m.id: m for m in self.modules}
        if self.entry not in self._by_id:
            raise KeyError(f"入口模块不存在: {self.entry}")

    def get(self, module_id: str) -> Module:
        if module_id not in self._by_id:
            raise KeyError(f"未知模块 id: {module_id}，可选: {list(self._by_id)}")
        return self._by_id[module_id]


def goto(module_id: str) -> Callable[[FlowContext, Any], str]:
    """生成固定跳转函数，便于写在 success/fail 上。"""

    def _goto(_ctx: FlowContext, _value: Any = None) -> str:
        return module_id

    return _goto
