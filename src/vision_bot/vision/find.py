"""识图 API（与运行时上下文无关，统一返回 Result）。"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from pathlib import Path

from vision_bot.core.models import MatchOptions, MatchResult
from vision_bot.core.vision.match import find_all_images, find_image_with_options
from vision_bot.runtime.cancel import raise_if_cancelled
from vision_bot.runtime.result import Result
from vision_bot.vision.session import session

logger = logging.getLogger(__name__)


def resolve_path(image: str | Path, base_dir: Path | None = None) -> Path:
    """将模板图路径解析为绝对路径。"""
    root = base_dir if base_dir is not None else session().base_dir
    path = Path(image)
    if path.is_absolute():
        return path
    if root is None:
        return path.resolve()
    return (root / path).resolve()


def _merge_options(
    defaults: MatchOptions | None,
    *,
    threshold: float | None = None,
    timeout: float | None = None,
    interval: float | None = None,
    region: tuple[int, int, int, int] | None = None,
    region_fit: bool | None = None,
    grayscale: bool | None = None,
) -> MatchOptions:
    opts = (defaults or MatchOptions()).model_copy(deep=True)
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
    return opts


def search(
    *images: str | Path,
    base_dir: Path | None = None,
    defaults: MatchOptions | None = None,
    cancelled: Callable[[], bool] | None = None,
    timeout: float | None = None,
    threshold: float | None = None,
    interval: float | None = None,
    region: tuple[int, int, int, int] | None = None,
    grayscale: bool | None = None,
) -> Result:
    """识图核心：在超时内轮询一张或多张模板，任一命中即返回。"""
    if not images:
        return Result.fail("未指定模板图")

    opts = _merge_options(
        defaults,
        threshold=threshold,
        timeout=0.0,
        interval=interval,
        region=region,
        grayscale=grayscale,
    )
    wait = opts.timeout if timeout is None else timeout
    poll = opts.interval
    labels = "/".join(Path(p).name for p in images)
    deadline = time.monotonic() + max(wait, 0.0)
    last: MatchResult | None = None

    while True:
        raise_if_cancelled(cancelled)
        for image in images:
            path = resolve_path(image, base_dir)
            hit = find_image_with_options(path, opts, cancelled=cancelled)
            last = hit
            if hit.found:
                if len(images) > 1:
                    logger.info("命中 [%s]", path.name)
                return Result.success(value=hit)
        if wait <= 0 or time.monotonic() >= deadline:
            logger.info("未找到 [%s]", labels)
            return Result.fail(f"识图未找到 [{labels}]", value=last)
        raise_if_cancelled(cancelled)
        time.sleep(poll)


def find(
    *images: str | Path,
    timeout: float | None = None,
    threshold: float | None = None,
    interval: float | None = None,
    region: tuple[int, int, int, int] | None = None,
    grayscale: bool | None = None,
) -> Result:
    """在屏幕上查找模板图（默认等 3 秒、每 0.5 秒查一次）。

    可传一张或多张模板；多图时每一轮按顺序尝试，任一命中即返回。
    """
    cfg = session()
    return search(
        *images,
        base_dir=cfg.base_dir,
        defaults=cfg.options,
        cancelled=cfg.cancelled,
        timeout=timeout,
        threshold=threshold,
        interval=interval,
        region=region,
        grayscale=grayscale,
    )


def find_all(
    image: str | Path,
    *,
    threshold: float | None = None,
    max_count: int = 32,
) -> Result:
    """查找屏幕上所有高于阈值的匹配（多目标）。"""
    cfg = session()
    path = resolve_path(image)
    th = cfg.options.threshold if threshold is None else threshold
    hits = find_all_images(
        path,
        threshold=th,
        region=cfg.options.region,
        region_fit=cfg.options.region_fit,
        grayscale=cfg.options.grayscale,
        max_count=max_count,
    )
    if hits:
        return Result.success(value=hits)
    return Result.fail(f"识图未找到 [{path.name}]")
