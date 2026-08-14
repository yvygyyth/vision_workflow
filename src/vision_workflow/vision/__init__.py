"""独立识图方法：在屏幕（或指定区域）中查找模板图。"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any

from vision_workflow.models.flow import MatchOptions, MatchResult

if TYPE_CHECKING:
    from PIL import Image

logger = logging.getLogger(__name__)


def find_image(
    template: str | Path,
    *,
    threshold: float = 0.8,
    timeout: float = 0.0,
    interval: float = 0.5,
    region: tuple[int, int, int, int] | None = None,
    grayscale: bool = True,
    screenshot: "Image.Image | None" = None,
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
        grayscale=grayscale,
    )
    deadline = time.monotonic() + max(options.timeout, 0.0)
    last: MatchResult | None = None

    while True:
        last = _match_once(path, options, screenshot=screenshot)
        if last.found:
            return last
        if options.timeout <= 0 or time.monotonic() >= deadline:
            return last or MatchResult(found=False, image=str(path), message="未匹配到")
        time.sleep(options.interval)


def find_image_with_options(
    template: str | Path,
    options: MatchOptions,
    *,
    screenshot: "Image.Image | None" = None,
) -> MatchResult:
    return find_image(
        template,
        threshold=options.threshold,
        timeout=options.timeout,
        interval=options.interval,
        region=options.region,
        grayscale=options.grayscale,
        screenshot=screenshot,
    )


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

    if screenshot is not None:
        hay_rgb = screenshot.convert("RGB")
        hay_bgr = cv2.cvtColor(np.array(hay_rgb), cv2.COLOR_RGB2BGR)
        offset_x, offset_y = 0, 0
        if options.region:
            left, top, width, height = options.region
            hay_bgr = hay_bgr[top : top + height, left : left + width]
            offset_x, offset_y = left, top
    else:
        bbox = None
        offset_x, offset_y = 0, 0
        if options.region:
            left, top, width, height = options.region
            bbox = (left, top, left + width, top + height)
            offset_x, offset_y = left, top
        grab = ImageGrab.grab(bbox=bbox)
        hay_bgr = cv2.cvtColor(np.array(grab.convert("RGB")), cv2.COLOR_RGB2BGR)

    from vision_workflow.display import match_scales

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


def _resize_template(cv2: Any, template_bgr: Any, scale: float) -> Any:
    if abs(scale - 1.0) < 1e-3:
        return template_bgr
    th0, tw0 = template_bgr.shape[:2]
    nw = max(1, int(round(tw0 * scale)))
    nh = max(1, int(round(th0 * scale)))
    interpolation = cv2.INTER_AREA if scale < 1.0 else cv2.INTER_LINEAR
    return cv2.resize(template_bgr, (nw, nh), interpolation=interpolation)
