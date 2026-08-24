"""任务启动时绑定 vision / events 默认值。"""

from __future__ import annotations

from vision_bot.events import bind as bind_events
from vision_bot.runtime.context import RunContext
from vision_bot.vision import bind as bind_vision


def bind_runtime(ctx: RunContext) -> None:
    bind_vision(base_dir=ctx.base_dir, options=ctx.defaults, cancelled=ctx.cancelled)
    bind_events(cancelled=ctx.cancelled)
