"""图转文字（本地免费 OCR：RapidOCR）。"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from PIL import Image

logger = logging.getLogger(__name__)

_engine: Any | None = None


def _get_engine() -> Any:
    global _engine
    if _engine is not None:
        return _engine
    try:
        from rapidocr import RapidOCR
    except ImportError as exc:
        raise RuntimeError(
            "OCR 依赖未安装，请执行: pip install rapidocr onnxruntime"
        ) from exc
    _engine = RapidOCR()
    return _engine


def _texts_from_result(result: Any) -> list[str]:
    """兼容 RapidOCR 3.x Output 与旧版 list 返回值。"""
    if result is None:
        return []

    txts = getattr(result, "txts", None)
    if txts is not None:
        return [str(t).strip() for t in txts if str(t).strip()]

    # 旧版: ( [[box, text, score], ...], elapse ) 或直接 list
    rows = result
    if isinstance(result, tuple) and result:
        rows = result[0]
    if not rows:
        return []

    parts: list[str] = []
    for item in rows:
        if not item or len(item) < 2:
            continue
        text = str(item[1]).strip()
        if text:
            parts.append(text)
    return parts


def image_to_text(
    image: "Image.Image | str | Path",
    *,
    join_with: str = "",
    use_det: bool = False,
) -> str:
    """将图片转为文字（本地 RapidOCR，免费离线）。

    Parameters
    ----------
    image:
        PIL Image，或图片路径。
    join_with:
        多行/多块文字的拼接符；默认直接拼接。
    use_det:
        是否先做文字检测。默认 ``False``（整图直接识别），
        适合已裁好的单行标题；整屏多行文字可传 ``True``。
    """
    import numpy as np
    from PIL import Image

    if isinstance(image, (str, Path)):
        path = Path(image)
        if not path.exists():
            raise FileNotFoundError(f"图片不存在: {path}")
        pil = Image.open(path).convert("RGB")
    else:
        pil = image.convert("RGB")

    arr = np.asarray(pil)
    result = _get_engine()(arr, use_det=use_det)
    parts = _texts_from_result(result)
    text = join_with.join(parts)
    logger.debug("image_to_text → %r", text)
    return text
