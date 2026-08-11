"""流程运行时上下文：识图、鼠标、复用能力。"""

from __future__ import annotations

import logging
import time
from pathlib import Path

from vision_workflow.input import Mouse
from vision_workflow.models.flow import MatchOptions, MatchResult
from vision_workflow.vision import find_image_with_options

logger = logging.getLogger(__name__)


class FlowContext:
    """模块 action / judge 里使用的运行时上下文。"""

    def __init__(
        self,
        *,
        base_dir: Path,
        dry_run: bool = False,
        defaults: MatchOptions | None = None,
    ) -> None:
        self.base_dir = base_dir
        self.dry_run = dry_run
        self.defaults = defaults or MatchOptions()
        self.vars: dict = {}

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
        grayscale: bool | None = None,
        match: MatchOptions | None = None,
    ) -> MatchResult:
        """独立识图方法。"""
        opts = self.defaults.model_copy(deep=True)
        if match is not None:
            opts = MatchOptions.model_validate({**opts.model_dump(), **match.model_dump(exclude_unset=True)})
        if threshold is not None:
            opts.threshold = threshold
        if timeout is not None:
            opts.timeout = timeout
        if interval is not None:
            opts.interval = interval
        if region is not None:
            opts.region = region
        if grayscale is not None:
            opts.grayscale = grayscale
        return find_image_with_options(self.resolve(image), opts)

    def mouse(self) -> Mouse:
        """新建一条鼠标链（记得末尾 .perform()）。"""
        return Mouse(dry_run=self.dry_run)

    def click_image(self, image: str | Path, **find_kwargs) -> MatchResult:
        """复用：找到图并点击中心。"""
        hit = self.find(image, **find_kwargs)
        if hit.found and hit.center:
            self.mouse().at(hit.center).click().perform()
        return hit

    def sleep(self, seconds: float) -> None:
        if self.dry_run:
            logger.info("(dry-run) sleep %.3fs", seconds)
            return
        time.sleep(seconds)

    def log(self, message: str, *args) -> None:
        logger.info(message, *args)
