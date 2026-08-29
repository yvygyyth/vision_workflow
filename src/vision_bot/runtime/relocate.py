"""画面重定位规则：按序匹配 when(ctx)，命中则取 then。"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass

from vision_bot.runtime.context import RunContext
from vision_bot.runtime.jump import Relocate

WhenFn = Callable[[RunContext], bool]
ThenValue = str | Relocate | None


@dataclass(frozen=True, slots=True)
class RelocateRule:
    """一条重定位规则。

    Attributes
    ----------
    when:
        仅接收 ``ctx``，返回是否命中。
    then:
        命中后的目标节点 id、:class:`Relocate` 或 ``None``（命中但不跳转）。
    """

    when: WhenFn
    then: ThenValue


def resolve(
    rules: Sequence[RelocateRule] | None,
    ctx: RunContext,
) -> ThenValue:
    """按数组顺序求值：第一个 ``when`` 为真则返回其 ``then``；皆未命中返回 ``None``。"""
    if not rules:
        return None
    for rule in rules:
        ctx.check_cancelled()
        if rule.when(ctx):
            return rule.then
    return None
