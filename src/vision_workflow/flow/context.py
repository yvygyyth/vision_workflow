"""流程运行时上下文：识图、鼠标、日志。"""

from __future__ import annotations

import logging
import time
from pathlib import Path

from vision_workflow.input import Mouse
from vision_workflow.models.flow import MatchOptions, MatchResult
from vision_workflow.vision import find_image_with_options

logger = logging.getLogger(__name__)


class FlowContext:
    """模块 event 使用的运行时上下文。"""

    def __init__(
        self,
        *,
        base_dir: Path,
        defaults: MatchOptions | None = None,
    ) -> None:
        self.base_dir = base_dir
        self.defaults = defaults or MatchOptions()
        self.vars: dict = {}
        self.params: dict = {}

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
        """独立识图方法。"""
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

    def mouse(self) -> Mouse:
        """新建一条鼠标链（记得末尾 .perform()）。"""
        return Mouse()

    def sleep(self, seconds: float) -> None:
        time.sleep(seconds)

    def log(self, message: str, *args) -> None:
        logger.info(message, *args)
