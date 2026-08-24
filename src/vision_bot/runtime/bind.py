"""任务启动时绑定 vision / events 默认值。"""

from __future__ import annotations

from vision_bot.events import bind as bind_events
from vision_bot.runtime.context import RunContext
from vision_bot.vision import bind as bind_vision


def bind_runtime(ctx: RunContext) -> None:
    """从运行上下文注入 vision / events 模块默认值。

    由 :func:`~vision_bot.runtime.runner.run` 在任务开始时自动调用，
    一般无需手动调用。

    Parameters
    ----------
    ctx:
        当前任务运行上下文。会将其 ``base_dir``、``defaults``、
        ``cancelled`` 分别绑定到识图与输入事件模块。
    """
    bind_vision(base_dir=ctx.base_dir, options=ctx.defaults, cancelled=ctx.cancelled)
    bind_events(cancelled=ctx.cancelled)
