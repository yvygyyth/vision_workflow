"""识图业务 API：单图 / 多图共用底层原语，快慢只靠 ``timeout``。

底层原语（``core.vision``）
----------------------------
- :func:`~vision_bot.core.vision.match.find_image`：单模板（可带 timeout）
- :func:`~vision_bot.core.vision.match.find_images`：多模板同帧批量（可带 timeout）

本模块
------
- :func:`find`：默认用会话 timeout（慢查）
- :func:`snap`：``timeout=0`` 的快查别名
"""

from __future__ import annotations

import time
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, cast, overload

from vision_bot.core.models import MatchResult
from vision_bot.core.vision.match import find_all_images, find_image, find_images
from vision_bot.runtime.result import Result
from vision_bot.vision.session import session

if TYPE_CHECKING:
    from PIL.Image import Image

ImageArg = str | Path
ImagesArg = ImageArg | Iterable[ImageArg]
Region = tuple[int, int, int, int]


def resolve_path(image: str | Path, base_dir: Path | None = None) -> Path:
    """将模板图路径解析为绝对路径。"""
    root = base_dir if base_dir is not None else session().base_dir
    path = Path(image)
    if path.is_absolute():
        return path
    if root is None:
        return path.resolve()
    return (root / path).resolve()


def _flatten_images(*images: ImagesArg) -> list[ImageArg]:
    out: list[ImageArg] = []
    for item in images:
        if isinstance(item, (str, Path)):
            out.append(item)
        else:
            out.extend(item)
    return out


def _match_to_result(hit: MatchResult) -> Result:
    name = Path(hit.image).name
    if hit.found:
        return Result.success(value=hit)
    return Result.fail(f"识图未找到 [{name}]", value=hit)


@dataclass
class ScreenSnapshot:
    """多模板同帧匹配结果：``path → Result``。"""

    hits: dict[str, Result] = field(default_factory=dict)
    ts: float = field(default_factory=time.monotonic)
    image: Image | None = None

    @property
    def race(self) -> bool:
        """任一模板命中（类比 ``Promise.race`` / ``any``）。"""
        return any(r.ok for r in self.hits.values())

    @property
    def all(self) -> bool:
        """全部模板命中（类比 ``Promise.all``）。"""
        return bool(self.hits) and all(r.ok for r in self.hits.values())

    def __getitem__(self, template: str) -> Result:
        hit = self.hits.get(template)
        if hit is None:
            return Result.fail(f"未匹配过模板 [{template}]")
        return hit

    def found(self, template: str) -> bool:
        hit = self.hits.get(template)
        return hit is not None and hit.ok

    def hit(self, template: str) -> Result | None:
        return self.hits.get(template)

    def center(self, template: str) -> tuple[int, int] | None:
        hit = self.hit(template)
        if hit is None or not hit.ok:
            return None
        mr = cast(MatchResult | None, hit.value)
        return None if mr is None else mr.center


def _run_lookup(
    *images: ImagesArg,
    timeout: float | None,
    threshold: float | None,
    interval: float | None,
    region: Region | None,
    grayscale: bool | None,
    screenshot: Image | None,
    cancelled: Callable[[], bool] | None,
) -> Result | ScreenSnapshot:
    flat = _flatten_images(*images)
    if not flat:
        return Result.fail("未指定模板图")

    cfg = session()
    opts = cfg.options
    wait = opts.timeout if timeout is None else timeout
    th = opts.threshold if threshold is None else threshold
    poll = opts.interval if interval is None else interval
    gray = opts.grayscale if grayscale is None else grayscale
    stop = cfg.cancelled if cancelled is None else cancelled
    keys = [str(p) for p in flat]
    abs_paths = [resolve_path(p) for p in flat]

    if len(abs_paths) == 1:
        hit = find_image(
            abs_paths[0],
            threshold=th,
            timeout=wait,
            interval=poll,
            region=region,
            region_fit=opts.region_fit,
            grayscale=gray,
            screenshot=screenshot,
            cancelled=stop,
        )
        return _match_to_result(hit)

    raw_hits, frame = find_images(
        abs_paths,
        keys=keys,
        threshold=th,
        timeout=wait,
        interval=poll,
        region=region,
        region_fit=opts.region_fit,
        grayscale=gray,
        screenshot=screenshot,
        cancelled=stop,
    )
    return ScreenSnapshot(
        hits={k: _match_to_result(v) for k, v in raw_hits.items()},
        image=frame,
    )


@overload
def find(
    image: str | Path,
    /,
    *,
    timeout: float | None = None,
    threshold: float | None = None,
    interval: float | None = None,
    region: Region | None = None,
    grayscale: bool | None = None,
    screenshot: Image | None = None,
) -> Result: ...


@overload
def find(
    *images: ImagesArg,
    timeout: float | None = None,
    threshold: float | None = None,
    interval: float | None = None,
    region: Region | None = None,
    grayscale: bool | None = None,
    screenshot: Image | None = None,
) -> Result | ScreenSnapshot: ...


def find(
    *images: ImagesArg,
    timeout: float | None = None,
    threshold: float | None = None,
    interval: float | None = None,
    region: Region | None = None,
    grayscale: bool | None = None,
    screenshot: Image | None = None,
    cancelled: Callable[[], bool] | None = None,
) -> Result | ScreenSnapshot:
    """识图（默认慢查：使用会话 ``timeout`` / ``interval``）。

    - 单图 → :class:`~vision_bot.runtime.result.Result`
    - 多图 → :class:`ScreenSnapshot`（同帧整表；慢查时轮询至任一命中或超时）
    """
    return _run_lookup(
        *images,
        timeout=timeout,
        threshold=threshold,
        interval=interval,
        region=region,
        grayscale=grayscale,
        screenshot=screenshot,
        cancelled=cancelled,
    )


@overload
def snap(
    image: str | Path,
    /,
    *,
    threshold: float | None = None,
    region: Region | None = None,
    grayscale: bool | None = None,
    screenshot: Image | None = None,
) -> Result: ...


@overload
def snap(
    *images: ImagesArg,
    threshold: float | None = None,
    region: Region | None = None,
    grayscale: bool | None = None,
    screenshot: Image | None = None,
) -> Result | ScreenSnapshot: ...


def snap(
    *images: ImagesArg,
    threshold: float | None = None,
    region: Region | None = None,
    grayscale: bool | None = None,
    screenshot: Image | None = None,
    cancelled: Callable[[], bool] | None = None,
) -> Result | ScreenSnapshot:
    """快查：等价于 ``find(..., timeout=0)``。"""
    return _run_lookup(
        *images,
        timeout=0.0,
        threshold=threshold,
        interval=None,
        region=region,
        grayscale=grayscale,
        screenshot=screenshot,
        cancelled=cancelled,
    )


def find_all(
    image: str | Path,
    *,
    threshold: float | None = None,
    max_count: int = 32,
) -> Result:
    """查找屏幕上所有高于阈值的匹配（多目标，同一模板）。"""
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
