"""一次截屏 + 批量匹配 → ScreenSnapshot。"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from vision_bot.core.models import MatchResult
from vision_bot.core.vision.match import find_image_with_options
from vision_bot.perception.signal import Signal, SignalRegistry

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


def capture(
    registry: SignalRegistry,
    base_dir: Path,
    signal_ids: set[str] | None = None,
    *,
    screenshot: Image.Image | None = None,
) -> ScreenSnapshot:
    """对指定 signals 批量匹配；screenshot 可复用同一张图。"""
    ids = sorted(signal_ids) if signal_ids is not None else registry.ids()
    img = screenshot if screenshot is not None else capture_screen()
    hits: dict[str, MatchResult] = {}

    for sid in ids:
        sig = registry.get(sid)
        template = registry.resolve_path(sid, base_dir)
        result = find_image_with_options(
            template,
            sig.match_options(),
            screenshot=img,
        )
        hits[sid] = result
        if result.found:
            logger.debug("snapshot hit %s conf=%.3f", sid, result.confidence)

    return ScreenSnapshot(hits=hits, image=img)


def refresh(
    snap: ScreenSnapshot,
    registry: SignalRegistry,
    base_dir: Path,
    signal_ids: set[str],
    *,
    new_screenshot: bool = True,
) -> ScreenSnapshot:
    """点击后局部重扫：默认重新截屏，只更新指定 signals。"""
    img = capture_screen() if new_screenshot else snap.image
    updated = dict(snap.hits)
    for sid in signal_ids:
        sig = registry.get(sid)
        template = registry.resolve_path(sid, base_dir)
        updated[sid] = find_image_with_options(
            template,
            sig.match_options(),
            screenshot=img,
        )
    return ScreenSnapshot(hits=updated, image=img)
