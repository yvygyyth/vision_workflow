"""识图与输入相关的数据类型。"""

from __future__ import annotations

from pydantic import BaseModel, Field


class MatchOptions(BaseModel):
    """识图匹配参数（可通过 :func:`vision.bind` 设为任务级默认值）。"""

    threshold: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="匹配分数下限（0~1），高于此值视为命中。",
    )
    timeout: float = Field(
        default=3.0,
        ge=0.0,
        description="最长等待秒数；0 表示只查找一次。",
    )
    interval: float = Field(
        default=0.5,
        ge=0.05,
        description="轮询间隔秒数（timeout > 0 时生效）。",
    )
    region: tuple[int, int, int, int] | None = Field(
        default=None,
        description="搜索区域 (left, top, width, height)；None 表示全屏。",
    )
    region_fit: bool = Field(
        default=True,
        description="是否按显示缩放比例适配 region（截屏时生效）。",
    )
    grayscale: bool = Field(
        default=True,
        description="是否转灰度后再匹配（更快、对色差更不敏感）。",
    )


class MatchResult(BaseModel):
    """单次模板匹配的结果。"""

    found: bool = Field(description="是否达到 threshold 视为命中。")
    image: str = Field(description="模板图路径字符串。")
    confidence: float = Field(default=0.0, description="最佳匹配的归一化分数（0~1）。")
    box: tuple[int, int, int, int] | None = Field(
        default=None,
        description="命中区域 (x, y, width, height)，未命中时为 None。",
    )
    center: tuple[int, int] | None = Field(
        default=None,
        description="命中区域中心点 (cx, cy)，未命中时为 None。",
    )
    message: str = Field(default="", description="匹配详情或失败原因。")
