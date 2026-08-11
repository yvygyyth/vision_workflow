"""动作执行器抽象与注册。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from vision_workflow.models import ActionPlan, ActionResult, ActionStatus, IntentType


class BaseAction(ABC):
    intent: IntentType

    def __init__(self, options: dict[str, Any] | None = None, dry_run: bool = False) -> None:
        self.options = options or {}
        self.dry_run = dry_run

    def run(self, plan: ActionPlan) -> ActionResult:
        enabled = bool(self.options.get("enabled", True))
        if not enabled:
            return ActionResult(
                plan_id=plan.id,
                intent=plan.intent,
                status=ActionStatus.SKIPPED,
                message=f"动作已禁用: {plan.intent.value}",
            )
        if self.dry_run:
            return ActionResult(
                plan_id=plan.id,
                intent=plan.intent,
                status=ActionStatus.DRY_RUN,
                message=f"(dry-run) 将执行 {plan.intent.value}",
                detail={"params": plan.params},
            )
        try:
            return self.execute(plan)
        except Exception as exc:  # noqa: BLE001 - 流水线需捕获并汇总
            return ActionResult(
                plan_id=plan.id,
                intent=plan.intent,
                status=ActionStatus.FAILED,
                message=str(exc),
            )

    @abstractmethod
    def execute(self, plan: ActionPlan) -> ActionResult:
        raise NotImplementedError


_REGISTRY: dict[IntentType, type[BaseAction]] = {}


def register_action(intent: IntentType):
    def decorator(cls: type[BaseAction]):
        cls.intent = intent
        _REGISTRY[intent] = cls
        return cls

    return decorator


def get_action(
    intent: IntentType,
    options: dict[str, Any] | None = None,
    dry_run: bool = False,
) -> BaseAction:
    if intent not in _REGISTRY:
        available = ", ".join(i.value for i in _REGISTRY) or "(empty)"
        raise KeyError(f"未知动作: {intent.value}，可选: {available}")
    return _REGISTRY[intent](options=options, dry_run=dry_run)


def list_actions() -> list[str]:
    return sorted(i.value for i in _REGISTRY)
