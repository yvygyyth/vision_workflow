"""动作执行上下文（供 actions / flows 使用）。"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from vision_bot.core.models import MatchOptions, MatchResult
from vision_bot.core.vision import find_image_with_options


@dataclass
class ActionContext:
    """运行时：识图、路径解析、临时变量。"""

    base_dir: Path
    defaults: MatchOptions = field(default_factory=MatchOptions)
    vars: dict[str, Any] = field(default_factory=dict)
    cancelled: Callable[[], bool] = field(default_factory=lambda: (lambda: False))
    reason: str = ""
    value: Any = None

    def resolve(self, image: str | Path) -> Path:
        path = Path(image)
        if path.is_absolute():
            return path
        return (self.base_dir / path).resolve()

    def find(
        self,
        image: str | Path,
        *,
        threshold: float | None = None,
        timeout: float | None = None,
        interval: float | None = None,
        region: tuple[int, int, int, int] | None = None,
        region_fit: bool | None = None,
        grayscale: bool | None = None,
        match: MatchOptions | None = None,
    ) -> MatchResult:
        opts = self.defaults.model_copy(deep=True)
        if match is not None:
            opts = MatchOptions.model_validate(
                {**opts.model_dump(), **match.model_dump(exclude_unset=True)}
            )
        if threshold is not None:
            opts.threshold = threshold
        if timeout is not None:
            opts.timeout = timeout
        if interval is not None:
            opts.interval = interval
        if region is not None:
            opts.region = region
        if region_fit is not None:
            opts.region_fit = region_fit
        if grayscale is not None:
            opts.grayscale = grayscale
        return find_image_with_options(self.resolve(image), opts)
