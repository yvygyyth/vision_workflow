"""内置动作实现。"""

from __future__ import annotations

import logging
import webbrowser
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from vision_workflow.actions import BaseAction, register_action
from vision_workflow.models import ActionPlan, ActionResult, ActionStatus, IntentType

logger = logging.getLogger(__name__)


@register_action(IntentType.OPEN_URL)
class OpenUrlAction(BaseAction):
    def execute(self, plan: ActionPlan) -> ActionResult:
        url = str(plan.params.get("url") or "").strip()
        if not url:
            raise ValueError("open_url 缺少 url 参数")

        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            raise ValueError(f"不允许的 URL scheme: {parsed.scheme}")

        allow_hosts = [str(h).lower() for h in self.options.get("allow_hosts") or []]
        host = (parsed.hostname or "").lower()
        if allow_hosts and host not in allow_hosts:
            raise PermissionError(f"主机不在白名单: {host}，允许: {allow_hosts}")

        opened = webbrowser.open(url)
        return ActionResult(
            plan_id=plan.id,
            intent=plan.intent,
            status=ActionStatus.SUCCESS if opened else ActionStatus.FAILED,
            message=f"已尝试打开 URL: {url}",
            detail={"url": url, "opened": opened},
        )


@register_action(IntentType.SAVE_FILE)
class SaveFileAction(BaseAction):
    def execute(self, plan: ActionPlan) -> ActionResult:
        filename = str(plan.params.get("filename") or "output.txt")
        content = str(plan.params.get("content") or "")
        output_dir = Path(str(self.options.get("output_dir") or "data/output"))
        if not output_dir.is_absolute():
            # 相对路径由调用方注入 root；此处兜底相对 cwd
            output_dir = Path.cwd() / output_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        # 防路径穿越
        target = (output_dir / Path(filename).name).resolve()
        if output_dir.resolve() not in target.parents and target != output_dir.resolve():
            raise PermissionError(f"非法输出路径: {target}")

        target.write_text(content, encoding="utf-8")
        return ActionResult(
            plan_id=plan.id,
            intent=plan.intent,
            status=ActionStatus.SUCCESS,
            message=f"已保存文件: {target}",
            detail={"path": str(target), "bytes": target.stat().st_size},
        )


@register_action(IntentType.CLICK_BUTTON)
class ClickButtonAction(BaseAction):
    def execute(self, plan: ActionPlan) -> ActionResult:
        target = plan.params.get("target")
        return ActionResult(
            plan_id=plan.id,
            intent=plan.intent,
            status=ActionStatus.SKIPPED,
            message="click_button 需要对接 GUI 自动化库后启用",
            detail={"target": target, "hint": "可接入 pyautogui / playwright"},
        )


@register_action(IntentType.NOTIFY)
class NotifyAction(BaseAction):
    def execute(self, plan: ActionPlan) -> ActionResult:
        message = str(plan.params.get("message") or "通知")
        logger.info("NOTIFY | %s", message)
        return ActionResult(
            plan_id=plan.id,
            intent=plan.intent,
            status=ActionStatus.SUCCESS,
            message=message,
            detail={"channel": "log"},
        )


@register_action(IntentType.UNKNOWN)
class UnknownAction(BaseAction):
    def execute(self, plan: ActionPlan) -> ActionResult:
        return ActionResult(
            plan_id=plan.id,
            intent=plan.intent,
            status=ActionStatus.SKIPPED,
            message="未知意图，已跳过执行",
            detail={"params": plan.params},
        )
