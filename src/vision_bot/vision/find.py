"""识图 API（与运行时上下文无关，统一返回 Result）。"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from pathlib import Path

from vision_bot.core.models import MatchOptions, MatchResult
from vision_bot.core.vision import find_all_images, find_image_with_options
from vision_bot.runtime.cancel import raise_if_cancelled
from vision_bot.runtime.result import Result
from vision_bot.vision.session import session

logger = logging.getLogger(__name__)


def resolve_path(image: str | Path, base_dir: Path | None = None) -> Path:
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


def find(
    image: str | Path,
    *,
    timeout: float | None = None,
    threshold: float | None = None,
    interval: float | None = None,
    region: tuple[int, int, int, int] | None = None,
    grayscale: bool | None = None,
) -> Result:
    """在屏幕上查找单张模板图；命中时 ``value`` 为 ``MatchResult``。"""
    cfg = session()
    path = resolve_path(image)
    opts = _merge_options(
        cfg.options,
        threshold=threshold,
        timeout=timeout,
        interval=interval,
        region=region,
        grayscale=grayscale,
    )
    hit = find_image_with_options(path, opts, cancelled=cfg.cancelled)
    if hit.found:
        return Result.success(value=hit)
    msg = hit.message or f"识图未找到 [{path.name}]"
    return Result.fail(msg, value=hit)


def wait_any(
    *images: str | Path,
    timeout: float = 3.0,
    threshold: float | None = None,
    interval: float | None = None,
    region: tuple[int, int, int, int] | None = None,
    grayscale: bool | None = None,
) -> Result:
    """超时内按顺序轮询多张模板；命中时 ``value`` 为 ``MatchResult``。"""
    if not images:
        return Result.fail("未指定模板图")
    cfg = session()
    labels = "/".join(Path(p).name for p in images)
    opts = _merge_options(
        cfg.options,
        threshold=threshold,
        timeout=0.0,
        interval=interval,
        region=region,
        grayscale=grayscale,
    )
    poll = opts.interval
    deadline = time.monotonic() + max(timeout, 0.0)
    last: MatchResult | None = None

    while True:
        raise_if_cancelled(cfg.cancelled)
        for image in images:
            path = resolve_path(image)
            hit = find_image_with_options(path, opts, cancelled=cfg.cancelled)
            last = hit
            if hit.found:
                if len(images) > 1:
                    logger.info("命中 [%s]", path.name)
                return Result.success(value=hit)
        if timeout <= 0 or time.monotonic() >= deadline:
            logger.info("未找到 [%s]", labels)
            return Result.fail(f"识图未找到 [{labels}]", value=last)
        raise_if_cancelled(cfg.cancelled)
        time.sleep(poll)


def find_all(
    image: str | Path,
    *,
    threshold: float | None = None,
    max_count: int = 32,
) -> Result:
    """查找所有高于阈值的匹配；命中时 ``value`` 为 ``list[MatchResult]``。"""
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


def _find_with(
    image: str | Path,
    *,
    base_dir: Path | None,
    options: MatchOptions | None,
    cancelled: Callable[[], bool] | None,
    timeout: float | None = None,
    threshold: float | None = None,
    interval: float | None = None,
    region: tuple[int, int, int, int] | None = None,
    grayscale: bool | None = None,
) -> Result:
    """动作链内部使用：显式传入 base_dir / options / cancelled。"""
    path = resolve_path(image, base_dir)
    opts = _merge_options(
        options,
        threshold=threshold,
        timeout=timeout,
        interval=interval,
        region=region,
        grayscale=grayscale,
    )
    hit = find_image_with_options(path, opts, cancelled=cancelled)
    if hit.found:
        return Result.success(value=hit)
    msg = hit.message or f"识图未找到 [{path.name}]"
    return Result.fail(msg, value=hit)


def _wait_any_with(
    *images: str | Path,
    base_dir: Path | None,
    options: MatchOptions | None,
    cancelled: Callable[[], bool] | None,
    timeout: float = 3.0,
    threshold: float | None = None,
    interval: float | None = None,
    region: tuple[int, int, int, int] | None = None,
    grayscale: bool | None = None,
) -> Result:
    if not images:
        return Result.fail("未指定模板图")
    labels = "/".join(Path(p).name for p in images)
    opts = _merge_options(
        options,
        threshold=threshold,
        timeout=0.0,
        interval=interval,
        region=region,
        grayscale=grayscale,
    )
    poll = opts.interval
    deadline = time.monotonic() + max(timeout, 0.0)
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
        if timeout <= 0 or time.monotonic() >= deadline:
            logger.info("未找到 [%s]", labels)
            return Result.fail(f"识图未找到 [{labels}]", value=last)
        raise_if_cancelled(cancelled)
        time.sleep(poll)
