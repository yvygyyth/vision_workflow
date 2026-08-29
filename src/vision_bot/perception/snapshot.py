"""一次截屏 + 按模板路径匹配 → ScreenSnapshot。"""

from __future__ import annotations

import logging
import time
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from vision_bot.core.models import MatchOptions, MatchResult
from vision_bot.core.vision.match import find_image_with_options
from vision_bot.perception.session import perception

if TYPE_CHECKING:
    from PIL import Image

logger = logging.getLogger(__name__)

Region = tuple[int, int, int, int]


@dataclass
class ScreenSnapshot:
    """当前画面感知结果；hits 的 key 为模板相对/绝对路径。"""

    hits: dict[str, MatchResult] = field(default_factory=dict)
    ts: float = field(default_factory=time.monotonic)
    image: Image.Image | None = None

    def found(self, template: str) -> bool:
        hit = self.hits.get(template)
        return hit is not None and hit.found

    def hit(self, template: str) -> MatchResult | None:
        return self.hits.get(template)

    def center(self, template: str) -> tuple[int, int] | None:
        hit = self.hit(template)
        if hit is None or not hit.found:
            return None
        return hit.center


def capture_screen() -> Image.Image:
    from PIL import ImageGrab

    return ImageGrab.grab().convert("RGB")


def resolve_template(template: str, base_dir: Path | None = None) -> Path:
    path = Path(template)
    if path.is_absolute():
        return path
    root = base_dir if base_dir is not None else perception().base_dir
    return (root / path).resolve()


def match(
    template: str,
    *,
    screenshot: Image.Image,
    threshold: float | None = None,
    region: Region | None = None,
    region_fit: bool = True,
    grayscale: bool | None = None,
    base_dir: Path | None = None,
) -> MatchResult:
    """在已有截图上匹配一张模板图。"""
    cat = perception() if base_dir is None else None
    root = base_dir if base_dir is not None else cat.base_dir  # type: ignore[union-attr]
    defaults = cat.defaults if cat is not None else MatchOptions()
    opts = MatchOptions(
        threshold=defaults.threshold if threshold is None else threshold,
        timeout=0.0,
        region=region,
        region_fit=region_fit,
        grayscale=defaults.grayscale if grayscale is None else grayscale,
    )
    return find_image_with_options(
        resolve_template(template, root),
        opts,
        screenshot=screenshot,
    )


def snap(
    templates: Iterable[str],
    *,
    screenshot: Image.Image | None = None,
    threshold: float | None = None,
    region: Region | None = None,
    region_fit: bool = True,
    grayscale: bool | None = None,
) -> ScreenSnapshot:
    """截屏并对给定模板路径批量匹配。"""
    paths = list(templates)
    img = screenshot if screenshot is not None else capture_screen()
    hits: dict[str, MatchResult] = {}
    for path in paths:
        result = match(
            path,
            screenshot=img,
            threshold=threshold,
            region=region,
            region_fit=region_fit,
            grayscale=grayscale,
        )
        hits[path] = result
        if result.found:
            logger.debug("snapshot hit %s conf=%.3f", path, result.confidence)
    return ScreenSnapshot(hits=hits, image=img)


def refresh(
    snap_result: ScreenSnapshot,
    templates: Iterable[str],
    *,
    new_screenshot: bool = True,
    threshold: float | None = None,
    region: Region | None = None,
) -> ScreenSnapshot:
    """点击后局部重扫：默认重新截屏，只更新指定模板。"""
    img = capture_screen() if new_screenshot else snap_result.image
    if img is None:
        img = capture_screen()
    updated = dict(snap_result.hits)
    for path in templates:
        updated[path] = match(
            path, screenshot=img, threshold=threshold, region=region
        )
    return ScreenSnapshot(hits=updated, image=img)
