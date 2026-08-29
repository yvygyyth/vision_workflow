"""感知层全局绑定：资源根路径 + 默认识图参数。"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from vision_bot.core.models import MatchOptions

_bound: PerceptionCatalog | None = None


@dataclass
class PerceptionCatalog:
    """进程/任务级感知配置（非单次 run 的会话状态）。"""

    base_dir: Path
    defaults: MatchOptions = field(default_factory=MatchOptions)


def bind_perception(
    base_dir: Path,
    *,
    defaults: MatchOptions | None = None,
) -> PerceptionCatalog:
    """任务启动时绑定（由 :func:`~vision_bot.runtime.runner.run` 调用）。"""
    global _bound
    catalog = PerceptionCatalog(
        base_dir=base_dir.resolve(),
        defaults=defaults if defaults is not None else MatchOptions(),
    )
    _bound = catalog
    return catalog


def perception() -> PerceptionCatalog:
    if _bound is None:
        raise RuntimeError("感知层未绑定，请在 run() 内执行或先调用 bind_perception")
    return _bound


def unbind_perception() -> None:
    """测试用：清除绑定。"""
    global _bound
    _bound = None
