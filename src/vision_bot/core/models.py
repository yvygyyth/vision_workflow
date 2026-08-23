"""识图与运行结果类型。"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class MatchOptions(BaseModel):
    threshold: float = Field(default=0.8, ge=0.0, le=1.0)
    timeout: float = Field(default=0.0, ge=0.0)
    interval: float = Field(default=0.5, ge=0.05)
    region: tuple[int, int, int, int] | None = None
    region_fit: bool = True
    grayscale: bool = True


class MatchResult(BaseModel):
    found: bool
    image: str
    confidence: float = 0.0
    box: tuple[int, int, int, int] | None = None
    center: tuple[int, int] | None = None
    message: str = ""


class StepResult(BaseModel):
    step: str
    success: bool = True
    message: str = ""


class RunResult(BaseModel):
    success: bool
    message: str = ""
    phases: list[str] = Field(default_factory=list)
    steps: list[StepResult] = Field(default_factory=list)
    value: Any = None
