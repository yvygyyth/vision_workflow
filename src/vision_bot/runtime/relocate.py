"""画面重定位规则：按序匹配 when(ctx)，命中则取 then。"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass

from vision_bot.runtime.context import RunContext
from vision_bot.runtime.result import Result, normalize_outcome

WhenFn = Callable[[RunContext], bool]
ThenValue = str | Result | None


@dataclass(frozen=True, slots=True)
class RelocateRule:
    """一条重定位规则。

    Attributes
    ----------
    when:
        仅接收 ``ctx``，返回是否命中。
    then:
        命中后的目标：节点 id、``Result`` 或 ``None``（命中但不跳转）。
        非 ``Result`` 的字符串会由 ``resolve`` 包装为 ``Result.success(then=...)``。
    """

    when: WhenFn
    then: ThenValue


def resolve(
    rules: Sequence[RelocateRule] | None,
    ctx: RunContext,
) -> Result | None:
    """求值 relocate 规则，返回归一后的 ``None | Result``。

    - ``rules is None``（未配置）：返回 ``None``，由 runner 从 ``children[0]`` 开跑。
    - 某条 ``when`` 命中：返回 ``normalize_outcome(then)``。
    - 已配置但全部未命中：返回 ``Result.fail``（交给父级 / call 方 relocate）。
    """
    if rules is None:
        return None
    for rule in rules:
        ctx.check_cancelled()
        if rule.when(ctx):
            return normalize_outcome(rule.then)
    return Result.fail("relocate 未命中")
