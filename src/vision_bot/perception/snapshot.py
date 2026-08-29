"""一次截屏 + 批量匹配 → ScreenSnapshot。"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from vision_bot.core.models import MatchResult
from vision_bot.core.vision.match import find_image_with_options
from vision_bot.perception.signal import SignalRegistry
from vision_bot.perception.session import perception

if TYPE_CHECKING:
    from PIL import Image

logger = logging.getLogger(__name__)


@dataclass
class ScreenSnapshot:
    """当前画面感知结果。"""

    hits: dict[str, MatchResult] = field(default_factory=dict)
    ts: float = field(default_factory=time.monotonic)
    image: Image.Image | None = None

    def found(self, signal_id: str) -> bool:
        hit = self.hits.get(signal_id)
        return hit is not None and hit.found

    def hit(self, signal_id: str) -> MatchResult | None:
        return self.hits.get(signal_id)

    def center(self, signal_id: str) -> tuple[int, int] | None:
        hit = self.hit(signal_id)
        if hit is None or not hit.found:
            return None
        return hit.center


def capture_screen() -> Image.Image:
    from PIL import ImageGrab

    return ImageGrab.grab().convert("RGB")


def match_signal(
    registry: SignalRegistry,
    base_dir: Path,
    signal_id: str,
    *,
    screenshot: Image.Image,
) -> MatchResult:
    """在已有截图上匹配单个 signal（显式传入目录；一般用 :func:`match`）。"""
    sig = registry.get(signal_id)
    template = registry.resolve_path(signal_id, base_dir)
    return find_image_with_options(
        template,
        sig.match_options(),
        screenshot=screenshot,
    )


def match(signal_id: str, *, screenshot: Image.Image) -> MatchResult:
    """用已绑定的感知目录，在截图上匹配单个 signal。"""
    cat = perception()
    return match_signal(cat.registry, cat.base_dir, signal_id, screenshot=screenshot)


def capture(
    registry: SignalRegistry,
    base_dir: Path,
    signal_ids: set[str] | None = None,
    *,
    screenshot: Image.Image | None = None,
) -> ScreenSnapshot:
    """对指定 signals 批量匹配（显式传入目录；一般用 :func:`snap`）。"""
    ids = sorted(signal_ids) if signal_ids is not None else registry.ids()
    img = screenshot if screenshot is not None else capture_screen()
    hits: dict[str, MatchResult] = {}

    for sid in ids:
        result = match_signal(registry, base_dir, sid, screenshot=img)
        hits[sid] = result
        if result.found:
            logger.debug("snapshot hit %s conf=%.3f", sid, result.confidence)

    return ScreenSnapshot(hits=hits, image=img)


def snap(
    signal_ids: set[str] | None = None,
    *,
    screenshot: Image.Image | None = None,
) -> ScreenSnapshot:
    """截屏并批量匹配；使用已绑定的感知目录。"""
    cat = perception()
    return capture(cat.registry, cat.base_dir, signal_ids, screenshot=screenshot)


def refresh(
    snap_result: ScreenSnapshot,
    signal_ids: set[str],
    *,
    new_screenshot: bool = True,
    registry: SignalRegistry | None = None,
    base_dir: Path | None = None,
) -> ScreenSnapshot:
    """点击后局部重扫：默认重新截屏，只更新指定 signals。"""
    if registry is None or base_dir is None:
        cat = perception()
        registry = registry or cat.registry
        base_dir = base_dir or cat.base_dir
    img = capture_screen() if new_screenshot else snap_result.image
    if img is None:
        img = capture_screen()
    updated = dict(snap_result.hits)
    for sid in signal_ids:
        updated[sid] = match_signal(registry, base_dir, sid, screenshot=img)
    return ScreenSnapshot(hits=updated, image=img)
