"""识图模块运行时默认值（任务启动时 bind 一次）。"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from vision_bot.core.models import MatchOptions


@dataclass
class VisionSession:
    base_dir: Path | None = None
    options: MatchOptions = field(default_factory=MatchOptions)
    cancelled: Callable[[], bool] | None = None


_session = VisionSession()


def bind(
    *,
    base_dir: Path | None = None,
    options: MatchOptions | None = None,
    cancelled: Callable[[], bool] | None = None,
) -> None:
    if base_dir is not None:
        _session.base_dir = base_dir
    if options is not None:
        _session.options = options
    if cancelled is not None:
        _session.cancelled = cancelled


def session() -> VisionSession:
    return _session
