"""独立识图方法：在屏幕（或指定区域）中查找模板图。"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any

from vision_bot.core.models import MatchOptions, MatchResult
from vision_bot.runtime.cancel import raise_if_cancelled

if TYPE_CHECKING:
    from PIL import Image

logger = logging.getLogger(__name__)


def find_image(
    template: str | Path,
    *,
    threshold: float = 0.8,
    timeout: float = 3.0,
    interval: float = 0.5,
    region: tuple[int, int, int, int] | None = None,
    region_fit: bool = True,
    grayscale: bool = True,
    screenshot: "Image.Image | None" = None,
    cancelled: Callable[[], bool] | None = None,
) -> MatchResult:
    """在屏幕或给定截图中查找模板图。

    Parameters
    ----------
    template:
        模板图片路径。
    threshold:
        匹配分数下限（0~1）。
    timeout:
        等待出现的最长时间；0 表示只查找一次。
    interval:
        轮询间隔。
    region:
        (left, top, width, height)；None 表示全屏。
        相对模板基准分辨率标定；截屏时默认按显示缩放（region_fit）。
    region_fit:
        截屏时是否缩放 region；传入 screenshot 时按图素坐标，不缩放。
    grayscale:
        是否灰度匹配（更快、对色彩不敏感）。
    screenshot:
        若传入则不截屏，直接在该图上匹配（便于测试）。
    """
    path = Path(template).expanduser()
    if not path.exists():
        return MatchResult(found=False, image=str(path), message=f"模板不存在: {path}")

    options = MatchOptions(
        threshold=threshold,
        timeout=timeout,
        interval=interval,
        region=region,
        region_fit=region_fit,
        grayscale=grayscale,
    )
    deadline = time.monotonic() + max(options.timeout, 0.0)
    last: MatchResult | None = None

    while True:
        raise_if_cancelled(cancelled)
        last = _match_once(path, options, screenshot=screenshot)
        if last.found:
            return last
        if options.timeout <= 0 or time.monotonic() >= deadline:
            return last or MatchResult(found=False, image=str(path), message="未匹配到")
        raise_if_cancelled(cancelled)
        time.sleep(options.interval)


def find_images(
    templates: list[str | Path] | tuple[str | Path, ...],
    *,
    keys: list[str] | None = None,
    threshold: float = 0.8,
    timeout: float = 0.0,
    interval: float = 0.5,
    region: tuple[int, int, int, int] | None = None,
    region_fit: bool = True,
    grayscale: bool = True,
    screenshot: "Image.Image | None" = None,
    cancelled: Callable[[], bool] | None = None,
) -> tuple[dict[str, MatchResult], "Image.Image | None"]:
    """多模板同帧批量匹配（原语）。

    每一轮只截（或复用）一帧，再对全部模板匹配。``timeout=0`` 只查一轮；
    ``timeout>0`` 时按 ``interval`` 轮询，**任一命中**或到期后返回该轮整表结果。

    Returns
    -------
    hits, frame
        ``hits`` 的 key 为 ``keys``（缺省为 ``str(template)``）；``frame`` 为最后一轮截图。
    """
    if not templates:
        return {}, screenshot

    label_keys = keys if keys is not None else [str(t) for t in templates]
    if len(label_keys) != len(templates):
        raise ValueError("keys 长度必须与 templates 一致")

    paths = [Path(t).expanduser() for t in templates]
    options = MatchOptions(
        threshold=threshold,
        timeout=timeout,
        interval=interval,
        region=region,
        region_fit=region_fit,
        grayscale=grayscale,
    )
    deadline = time.monotonic() + max(options.timeout, 0.0)
    last_hits: dict[str, MatchResult] = {}
    last_frame: Image.Image | None = screenshot

    while True:
        raise_if_cancelled(cancelled)
        if screenshot is not None:
            frame = screenshot
        else:
            from PIL import ImageGrab

            frame = ImageGrab.grab().convert("RGB")
        last_frame = frame

        hits: dict[str, MatchResult] = {}
        any_found = False
        for key, path in zip(label_keys, paths, strict=True):
            if not path.exists():
                hit = MatchResult(
                    found=False, image=str(path), message=f"模板不存在: {path}"
                )
            else:
                hit = _match_once(path, options, screenshot=frame)
            hits[key] = hit
            if hit.found:
                any_found = True
        last_hits = hits

        if any_found or options.timeout <= 0 or time.monotonic() >= deadline:
            return last_hits, last_frame
        raise_if_cancelled(cancelled)
        time.sleep(options.interval)


def _resolve_region(
    options: MatchOptions,
    *,
    screenshot: "Image.Image | None",
) -> tuple[int, int, int, int] | None:
    """截屏匹配时对 region 做显示缩放；给定 screenshot 时按图素坐标。"""
    if not options.region:
        return None
    if screenshot is not None:
        return options.region
    from vision_bot.core.display import fit_region

    return fit_region(options.region, fit=options.region_fit)


def _match_once(
    path: Path,
    options: MatchOptions,
    *,
    screenshot: "Image.Image | None" = None,
) -> MatchResult:
    try:
        import cv2
        import numpy as np
        from PIL import ImageGrab
    except ImportError as exc:
        raise RuntimeError(
            "识图依赖未安装，请执行: pip install opencv-python-headless numpy"
        ) from exc

    template_bgr = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if template_bgr is None:
        return MatchResult(found=False, image=str(path), message=f"无法读取模板: {path}")

    region = _resolve_region(options, screenshot=screenshot)

    if screenshot is not None:
        hay_rgb = screenshot.convert("RGB")
        hay_bgr = cv2.cvtColor(np.array(hay_rgb), cv2.COLOR_RGB2BGR)
        offset_x, offset_y = 0, 0
        if region:
            left, top, width, height = region
            hay_bgr = hay_bgr[top : top + height, left : left + width]
            offset_x, offset_y = left, top
    else:
        bbox = None
        offset_x, offset_y = 0, 0
        if region:
            left, top, width, height = region
            bbox = (left, top, left + width, top + height)
            offset_x, offset_y = left, top
        grab = ImageGrab.grab(bbox=bbox)
        hay_bgr = cv2.cvtColor(np.array(grab.convert("RGB")), cv2.COLOR_RGB2BGR)

    from vision_bot.core.display import match_scales

    hay = (
        cv2.cvtColor(hay_bgr, cv2.COLOR_BGR2GRAY)
        if options.grayscale
        else hay_bgr
    )
    hh, hw = hay.shape[:2]

    best: dict[str, Any] | None = None
    for scale in match_scales():
        tpl_bgr = _resize_template(cv2, template_bgr, scale)
        tpl = (
            cv2.cvtColor(tpl_bgr, cv2.COLOR_BGR2GRAY)
            if options.grayscale
            else tpl_bgr
        )
        th, tw = tpl.shape[:2]
        if th > hh or tw > hw or th < 1 or tw < 1:
            continue

        result = cv2.matchTemplate(hay, tpl, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        confidence = float(max_val)
        if best is None or confidence > best["confidence"]:
            x, y = int(max_loc[0] + offset_x), int(max_loc[1] + offset_y)
            best = {
                "confidence": confidence,
                "scale": scale,
                "box": (x, y, tw, th),
                "center": (x + tw // 2, y + th // 2),
            }

    if best is None:
        return MatchResult(
            found=False,
            image=str(path),
            message="多尺度下模板均大于搜索区域或无效",
        )

    confidence = best["confidence"]
    scale = best["scale"]
    box = best["box"]
    center = best["center"]
    found = confidence >= options.threshold
    logger.debug(
        "find_image %s conf=%.3f threshold=%.3f scale=%.3f found=%s center=%s",
        path.name,
        confidence,
        options.threshold,
        scale,
        found,
        center if found else None,
    )
    return MatchResult(
        found=found,
        image=str(path),
        confidence=confidence,
        box=box if found else None,
        center=center if found else None,
        message="matched" if found else f"confidence {confidence:.3f} < {options.threshold}",
    )


def find_all_images(
    template: str | Path,
    *,
    threshold: float = 0.8,
    region: tuple[int, int, int, int] | None = None,
    region_fit: bool = True,
    grayscale: bool = True,
    screenshot: "Image.Image | None" = None,
    max_count: int = 32,
) -> list[MatchResult]:
    """查找所有高于阈值的匹配（多尺度 + 简易 NMS），按置信度降序。"""
    path = Path(template).expanduser()
    if not path.exists():
        return []

    options = MatchOptions(
        threshold=threshold,
        timeout=0.0,
        interval=0.5,
        region=region,
        region_fit=region_fit,
        grayscale=grayscale,
    )
    return _match_all(path, options, screenshot=screenshot, max_count=max_count)


def _match_all(
    path: Path,
    options: MatchOptions,
    *,
    screenshot: "Image.Image | None" = None,
    max_count: int = 32,
) -> list[MatchResult]:
    try:
        import cv2
        import numpy as np
        from PIL import ImageGrab
    except ImportError as exc:
        raise RuntimeError(
            "识图依赖未安装，请执行: pip install opencv-python-headless numpy"
        ) from exc

    template_bgr = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if template_bgr is None:
        return []

    region = _resolve_region(options, screenshot=screenshot)

    if screenshot is not None:
        hay_rgb = screenshot.convert("RGB")
        hay_bgr = cv2.cvtColor(np.array(hay_rgb), cv2.COLOR_RGB2BGR)
        offset_x, offset_y = 0, 0
        if region:
            left, top, width, height = region
            hay_bgr = hay_bgr[top : top + height, left : left + width]
            offset_x, offset_y = left, top
    else:
        bbox = None
        offset_x, offset_y = 0, 0
        if region:
            left, top, width, height = region
            bbox = (left, top, left + width, top + height)
            offset_x, offset_y = left, top
        grab = ImageGrab.grab(bbox=bbox)
        hay_bgr = cv2.cvtColor(np.array(grab.convert("RGB")), cv2.COLOR_RGB2BGR)

    from vision_bot.core.display import match_scales

    hay = (
        cv2.cvtColor(hay_bgr, cv2.COLOR_BGR2GRAY)
        if options.grayscale
        else hay_bgr
    )
    hh, hw = hay.shape[:2]
    candidates: list[dict[str, Any]] = []

    for scale in match_scales():
        tpl_bgr = _resize_template(cv2, template_bgr, scale)
        tpl = (
            cv2.cvtColor(tpl_bgr, cv2.COLOR_BGR2GRAY)
            if options.grayscale
            else tpl_bgr
        )
        th, tw = tpl.shape[:2]
        if th > hh or tw > hw or th < 1 or tw < 1:
            continue

        result = cv2.matchTemplate(hay, tpl, cv2.TM_CCOEFF_NORMED)
        ys, xs = np.where(result >= options.threshold)
        for y, x in zip(ys.tolist(), xs.tolist(), strict=False):
            conf = float(result[y, x])
            bx = int(x + offset_x)
            by = int(y + offset_y)
            candidates.append(
                {
                    "confidence": conf,
                    "scale": scale,
                    "box": (bx, by, tw, th),
                    "center": (bx + tw // 2, by + th // 2),
                }
            )

    kept = _nms_boxes(candidates, iou_threshold=0.35)
    kept.sort(key=lambda c: c["confidence"], reverse=True)
    if max_count > 0:
        kept = kept[:max_count]

    return [
        MatchResult(
            found=True,
            image=str(path),
            confidence=c["confidence"],
            box=c["box"],
            center=c["center"],
            message="matched",
        )
        for c in kept
    ]


def _box_iou(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> float:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    ax2, ay2 = ax + aw, ay + ah
    bx2, by2 = bx + bw, by + bh
    ix1, iy1 = max(ax, bx), max(ay, by)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    iw, ih = max(0, ix2 - ix1), max(0, iy2 - iy1)
    inter = iw * ih
    if inter <= 0:
        return 0.0
    union = aw * ah + bw * bh - inter
    return inter / union if union > 0 else 0.0


def _nms_boxes(
    candidates: list[dict[str, Any]],
    *,
    iou_threshold: float,
) -> list[dict[str, Any]]:
    ordered = sorted(candidates, key=lambda c: c["confidence"], reverse=True)
    kept: list[dict[str, Any]] = []
    for cand in ordered:
        if any(_box_iou(cand["box"], k["box"]) >= iou_threshold for k in kept):
            continue
        kept.append(cand)
    return kept


def _resize_template(cv2: Any, template_bgr: Any, scale: float) -> Any:
    if abs(scale - 1.0) < 1e-3:
        return template_bgr
    th0, tw0 = template_bgr.shape[:2]
    nw = max(1, int(round(tw0 * scale)))
    nh = max(1, int(round(th0 * scale)))
    interpolation = cv2.INTER_AREA if scale < 1.0 else cv2.INTER_LINEAR
    return cv2.resize(template_bgr, (nw, nh), interpolation=interpolation)


from vision_bot.core.vision.capture import grab_region
from vision_bot.core.vision.ocr import image_to_text

__all__ = [
    "find_image",
    "find_images",
    "find_all_images",
    "grab_region",
    "image_to_text",
]
