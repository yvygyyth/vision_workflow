"""将识别结果转为动作计划。"""

from __future__ import annotations

from vision_workflow.models import ActionPlan, IntentType, RecognitionResult


class Planner:
    """简单规划器：意图 + payload → ActionPlan。后续可扩展多步编排。"""

    def plan(self, recognition: RecognitionResult) -> ActionPlan:
        params = dict(recognition.payload)
        reason = f"由 {recognition.recognizer} 识别，置信度 {recognition.confidence:.2f}"

        if recognition.intent == IntentType.OPEN_URL and "url" not in params:
            # 尝试从文本中已由 recognizer 填入；否则保持空交由 action 报错
            pass
        if recognition.intent == IntentType.NOTIFY and "message" not in params:
            params["message"] = recognition.text or "空通知"
        if recognition.intent == IntentType.SAVE_FILE:
            params.setdefault("filename", "recognized.txt")
            params.setdefault("content", recognition.text)

        return ActionPlan(
            intent=recognition.intent,
            params=params,
            reason=reason,
            confidence=recognition.confidence,
        )
