"""屏幕区域截图。"""

from __future__ import annotations

from typing import TYPE_CHECKING

from vision_bot.core.display import fit_region

if TYPE_CHECKING:
    from PIL import Image

Region = tuple[int, int, int, int]


def grab_region(
    region: Region,
    *,
    region_fit: bool = True,
) -> "Image.Image":
    """截取屏幕指定区域，返回 PIL Image。

    Parameters
    ----------
    region:
        ``(left, top, width, height)``；相对模板基准分辨率标定。
    region_fit:
        是否按显示缩放换算 region（与识图 ``region_fit`` 一致）。
    """
    from PIL import ImageGrab

    left, top, width, height = fit_region(region, fit=region_fit)
    if width <= 0 or height <= 0:
        raise ValueError(f"无效 region 尺寸: {(left, top, width, height)}")
    bbox = (left, top, left + width, top + height)
    return ImageGrab.grab(bbox=bbox).convert("RGB")
