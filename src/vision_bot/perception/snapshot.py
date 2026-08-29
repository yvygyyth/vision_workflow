"""一次截屏 + 按模板路径批量匹配 → :class:`ScreenSnapshot`。

典型用法
--------
在 Flow / Module 里用 :func:`snap` 对一组模板做「同一帧」识别，再用
:meth:`ScreenSnapshot.found` / :meth:`~ScreenSnapshot.center` 做分支或点击：

.. code-block:: python

    shot = snap({SELECT_WU_JIANG, SWITCH})
    if not shot.found(SWITCH):
        return Result.fail("无 switch")
    c = shot.center(SELECT_WU_JIANG)

设计要点
--------
- **同一帧**：一次 ``snap`` 只截（或复用）一张屏，再对所有模板匹配，避免
  多次截屏导致状态不一致。
- **hits 的 key**：与传入的模板路径字符串完全一致（相对或绝对），查询时
  必须用同一字符串，不能混用「相对路径」和「resolve 后的绝对路径」。
- **默认参数**：``threshold`` / ``grayscale`` 未显式传入时，取自
  :func:`~vision_bot.perception.session.perception` 的全局 defaults。
"""

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
    from PIL.Image import Image

logger = logging.getLogger(__name__)

Region = tuple[int, int, int, int]
"""可选匹配区域 ``(left, top, right, bottom)``，屏幕像素坐标。"""


@dataclass
class ScreenSnapshot:
    """某一帧画面上的模板匹配结果集合。

    Attributes
    ----------
    hits:
        模板路径 → :class:`~vision_bot.core.models.MatchResult`。
        key 为调用 :func:`snap` / :func:`match` 时传入的原始路径字符串。
    ts:
        创建本快照时的 ``time.monotonic()``，便于排查耗时或过期判断。
    image:
        本帧截图（RGB）。``snap`` 总会填充；若自行构造可为空。
    """

    hits: dict[str, MatchResult] = field(default_factory=dict)
    ts: float = field(default_factory=time.monotonic)
    image: Image | None = None

    def found(self, template: str) -> bool:
        """指定模板是否在本帧匹配成功。

        Parameters
        ----------
        template:
            模板路径，须与 ``hits`` 的 key 一致。

        Returns
        -------
        bool
            有命中且 ``MatchResult.found`` 为真时返回 ``True``；
            未匹配过该路径、或匹配失败，均返回 ``False``。
        """
        hit = self.hits.get(template)
        return hit is not None and hit.found

    def hit(self, template: str) -> MatchResult | None:
        """返回指定模板的完整匹配结果（含置信度、中心点等）。

        Parameters
        ----------
        template:
            模板路径，须与 ``hits`` 的 key 一致。

        Returns
        -------
        MatchResult or None
            本帧对该路径做过匹配则返回对应结果（成功或失败都有）；
            从未匹配过该路径时返回 ``None``。
        """
        return self.hits.get(template)

    def center(self, template: str) -> tuple[int, int] | None:
        """匹配成功时返回模板中心点屏幕坐标 ``(x, y)``。

        Parameters
        ----------
        template:
            模板路径，须与 ``hits`` 的 key 一致。

        Returns
        -------
        tuple[int, int] or None
            未命中或未匹配过该路径时返回 ``None``。
        """
        hit = self.hit(template)
        if hit is None or not hit.found:
            return None
        return hit.center


def capture_screen() -> Image:
    """抓取当前全屏并转为 RGB。

    Returns
    -------
    PIL.Image.Image
        RGB 模式截图，供 :func:`match` / :func:`snap` 复用。
    """
    from PIL import ImageGrab

    return ImageGrab.grab().convert("RGB")


def resolve_template(template: str, base_dir: Path | None = None) -> Path:
    """将模板路径解析为绝对 ``Path``。

    Parameters
    ----------
    template:
        相对或绝对路径字符串。
    base_dir:
        相对路径的根目录。为 ``None`` 时使用
        :func:`~vision_bot.perception.session.perception` 的 ``base_dir``。

    Returns
    -------
    pathlib.Path
        绝对路径；绝对 ``template`` 原样 resolve，相对路径则拼在 ``base_dir`` 下。
    """
    path = Path(template)
    if path.is_absolute():
        return path
    root = base_dir if base_dir is not None else perception().base_dir
    return (root / path).resolve()


def match(
    template: str,
    *,
    screenshot: Image,
    threshold: float | None = None,
    region: Region | None = None,
    region_fit: bool = True,
    grayscale: bool | None = None,
    base_dir: Path | None = None,
) -> MatchResult:
    """在已有截图上匹配一张模板图（不再二次截屏）。

    Parameters
    ----------
    template:
        模板路径（相对或绝对）。
    screenshot:
        待匹配的画面；通常来自 :func:`capture_screen` 或上一帧 ``snap.image``。
    threshold:
        相似度阈值；``None`` 时用感知会话 defaults。
    region:
        可选搜索区域 ``(left, top, right, bottom)``；``None`` 表示全图。
    region_fit:
        区域与模板尺寸的适配策略，透传给底层识图。
    grayscale:
        是否灰度匹配；``None`` 时用感知会话 defaults。
    base_dir:
        解析相对模板路径的根；``None`` 时用感知会话 ``base_dir``。
        显式传入时不读会话 defaults，未给的 ``threshold`` / ``grayscale``
        回落到 :class:`~vision_bot.core.models.MatchOptions` 默认值。

    Returns
    -------
    MatchResult
        单次匹配结果（是否找到、置信度、中心点等）。
    """
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
    screenshot: Image | None = None,
    threshold: float | None = None,
    region: Region | None = None,
    region_fit: bool = True,
    grayscale: bool | None = None,
) -> ScreenSnapshot:
    """截一屏（或复用截图），对给定模板路径批量匹配。

    所有模板共用同一张图与同一套匹配参数，适合「这一帧上有没有 A/B/C」的判定。

    Parameters
    ----------
    templates:
        模板路径可迭代对象（常用 ``set`` / ``list``）。返回的 ``hits`` key
        与此处字符串一致。
    screenshot:
        若已有截图则直接使用，避免重复抓屏；``None`` 时调用
        :func:`capture_screen`。
    threshold:
        相似度阈值；``None`` 时用感知会话 defaults。
    region:
        可选搜索区域；``None`` 表示全图。整批模板共用。
    region_fit:
        区域适配策略，透传给每次 :func:`match`。
    grayscale:
        是否灰度匹配；``None`` 时用感知会话 defaults。

    Returns
    -------
    ScreenSnapshot
        含全部匹配结果与本帧 ``image``；命中项会打 debug 日志。
    """
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
