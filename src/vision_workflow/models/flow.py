"""流程 / 工作流运行结果类型。"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class MatchOptions(BaseModel):
    threshold: float = Field(default=0.8, ge=0.0, le=1.0)
    timeout: float = Field(default=0.0, ge=0.0)
    interval: float = Field(default=0.5, ge=0.05)
    region: tuple[int, int, int, int] | None = None
    """(left, top, width, height)；相对模板基准分辨率标定，截屏匹配时默认按显示缩放。"""
    region_fit: bool = True
    """截屏匹配时是否对 region 做显示缩放；传入 screenshot 时忽略（按图素坐标裁剪）。"""
    grayscale: bool = True


class MatchResult(BaseModel):
    found: bool
    image: str
    confidence: float = 0.0
    box: tuple[int, int, int, int] | None = None
    center: tuple[int, int] | None = None
    message: str = ""


class StepRunResult(BaseModel):
    step_id: str  # flow_id.module_id
    step_label: str = ""  # 可读：流程名/模块名
    success: bool = True
    message: str = ""
    feedback: str = ""
    value: Any = None


class FlowRunResult(BaseModel):
    flow_name: str
    success: bool
    message: str = ""
    feedback: str = ""
    path: list[str] = Field(default_factory=list)
    steps: list[StepRunResult] = Field(default_factory=list)
