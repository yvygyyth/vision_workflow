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
    """求值 relocate 规则。

    - ``rules is None``（未配置）：返回 ``None``，由 runner 从 ``children[0]`` 开跑。
    - 某条 ``when`` 命中：返回其 ``then``（可为 ``None`` / id / ``Relocate.PARENT``）。
    - 已配置但全部未命中：返回 ``Relocate.PARENT``（交给父级）。
    """
    if rules is None:
        return None
    for rule in rules:
        ctx.check_cancelled()
        if rule.when(ctx):
            return rule.then
    return Relocate.PARENT
