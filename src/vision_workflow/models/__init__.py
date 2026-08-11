"""领域模型导出。"""

from __future__ import annotations

from vision_workflow.models.flow import (
    Flow,
    FlowRunResult,
    MatchOptions,
    MatchResult,
    StepRunResult,
)

# 旧流水线兼容（可选）
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class IntentType(str, Enum):
    OPEN_URL = "open_url"
    SAVE_FILE = "save_file"
    CLICK_BUTTON = "click_button"
    NOTIFY = "notify"
    UNKNOWN = "unknown"


class ActionStatus(str, Enum):
    PENDING = "pending"
    SUCCESS = "success"
    SKIPPED = "skipped"
    FAILED = "failed"
    DRY_RUN = "dry_run"


class RecognitionResult(BaseModel):
    image_path: str
    text: str = ""
    intent: IntentType = IntentType.UNKNOWN
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    payload: dict[str, Any] = Field(default_factory=dict)
    raw: dict[str, Any] = Field(default_factory=dict)
    recognizer: str = "unknown"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ActionPlan(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex[:12])
    intent: IntentType
    params: dict[str, Any] = Field(default_factory=dict)
    reason: str = ""
    confidence: float = 0.0


class ActionResult(BaseModel):
    plan_id: str
    intent: IntentType
    status: ActionStatus
    message: str = ""
    detail: dict[str, Any] = Field(default_factory=dict)


class PipelineResult(BaseModel):
    run_id: str = Field(default_factory=lambda: uuid4().hex[:12])
    image_path: str
    recognition: RecognitionResult | None = None
    plan: ActionPlan | None = None
    action: ActionResult | None = None
    success: bool = False
    message: str = ""
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at: datetime | None = None

    def finish(self, success: bool, message: str = "") -> PipelineResult:
        self.success = success
        self.message = message
        self.finished_at = datetime.now(timezone.utc)
        return self


__all__ = [
    "Flow",
    "FlowRunResult",
    "MatchOptions",
    "MatchResult",
    "StepRunResult",
    "IntentType",
    "ActionStatus",
    "RecognitionResult",
    "ActionPlan",
    "ActionResult",
    "PipelineResult",
]
