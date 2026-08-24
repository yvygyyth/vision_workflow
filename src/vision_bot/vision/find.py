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
    """将模板图路径解析为绝对路径。

    Parameters
    ----------
    image:
        模板图路径。绝对路径原样返回；相对路径拼在 ``base_dir``（或已 bind
        的项目根）之下。
    base_dir:
        可选的项目根。未传时使用 :func:`vision.bind` 绑定的 ``base_dir``。

    Returns
    -------
    Path
        解析后的绝对路径。
    """
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
    """在屏幕上查找单张模板图。

    Parameters
    ----------
    image:
        模板图路径（相对路径相对于已 bind 的 ``base_dir``）。
    timeout:
        最长等待秒数。``None`` 继承 bind 的默认值；底层 ``0`` 表示只查一次。
    threshold:
        匹配分数下限（0~1）。``None`` 继承 bind 的默认值（通常 0.8）。
    interval:
        轮询间隔秒数。``None`` 继承 bind 的默认值（通常 0.5）。
    region:
        搜索区域 ``(left, top, width, height)``，像素坐标。
        ``None`` 表示全屏；``None`` 且未 bind 区域时搜全屏。
    grayscale:
        是否灰度匹配。``None`` 继承 bind 的默认值（通常 ``True``）。

    Returns
    -------
    Result
        命中：``ok=True``，``value`` 为 :class:`~vision_bot.core.models.MatchResult`。
        未命中：``ok=False``，``message`` 说明原因。
    """
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
    """在超时内按顺序轮询多张模板，任一命中即返回。

    每一轮按 ``images`` 从左到右依次尝试；全部未命中则 sleep 后进入下一轮。

    Parameters
    ----------
    *images:
        一个或多个模板图路径。至少传一张。
    timeout:
        最长等待秒数，默认 ``3.0``。
    threshold:
        匹配分数下限（0~1）。``None`` 继承 bind 默认值。
    interval:
        每轮之间的轮询间隔秒数。``None`` 继承 bind 默认值。
    region:
        搜索区域 ``(left, top, width, height)``。``None`` 表示全屏。
    grayscale:
        是否灰度匹配。``None`` 继承 bind 默认值。

    Returns
    -------
    Result
        命中：``ok=True``，``value`` 为命中的 :class:`~vision_bot.core.models.MatchResult`。
        超时：``ok=False``，``message`` 形如 ``识图未找到 [a.png/b.png]``。
    """
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
    """查找屏幕上所有高于阈值的匹配（多目标）。

    Parameters
    ----------
    image:
        模板图路径。
    threshold:
        匹配分数下限（0~1）。``None`` 继承 bind 默认值。
    max_count:
        最多返回的匹配数量，默认 ``32``。按置信度降序截断。

    Returns
    -------
    Result
        有匹配：``ok=True``，``value`` 为 ``list[MatchResult]``。
        无匹配：``ok=False``，``message`` 说明未找到。
    """
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
