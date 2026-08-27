"""任务启动时绑定 vision / events 默认值。"""

from __future__ import annotations

from vision_bot.actions.context import bind_action_context
from vision_bot.events import bind as bind_events
from vision_bot.runtime.context import RunContext
from vision_bot.vision import bind as bind_vision


def bind_runtime(ctx: RunContext) -> None:
    """从运行上下文注入 vision / events / 动作链默认值。

    由 :func:`~vision_bot.runtime.runner.run` 在任务开始时自动调用，
    一般无需手动调用。
    """
    bind_vision(base_dir=ctx.base_dir, options=ctx.defaults, cancelled=ctx.cancelled)
    bind_events(cancelled=ctx.cancelled)
    bind_action_context(
        base_dir=ctx.base_dir,
        defaults=ctx.defaults,
        vars=ctx.vars,
        cancelled=ctx.cancelled,
    )
