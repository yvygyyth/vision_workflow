"""识图执行主流水线。"""

from __future__ import annotations

import logging
from pathlib import Path

from vision_workflow.actions import get_action
from vision_workflow.config import RuntimeConfig
from vision_workflow.models import ActionStatus, PipelineResult
from vision_workflow.pipeline.planner import Planner
from vision_workflow.recognizers import get_recognizer

# 注册内置实现
import vision_workflow.actions.impl  # noqa: F401
import vision_workflow.recognizers.impl  # noqa: F401

logger = logging.getLogger(__name__)


class Pipeline:
    def __init__(self, config: RuntimeConfig) -> None:
        self.config = config
        self.planner = Planner()

        name = config.pipeline.recognizer
        options = dict(config.recognizers.get(name) or {})
        self.recognizer = get_recognizer(name, options=options)

    def run(self, image_path: str | Path) -> PipelineResult:
        path = Path(image_path).expanduser().resolve()
        result = PipelineResult(image_path=str(path))
        logger.info("开始流水线 | run_id=%s | image=%s", result.run_id, path)

        try:
            recognition = self.recognizer.recognize(path)
            result.recognition = recognition
            logger.info(
                "识别完成 | intent=%s | confidence=%.2f | text=%s",
                recognition.intent.value,
                recognition.confidence,
                (recognition.text[:80] + "…") if len(recognition.text) > 80 else recognition.text,
            )

            if recognition.confidence < self.config.pipeline.min_confidence:
                return result.finish(
                    False,
                    f"置信度 {recognition.confidence:.2f} 低于阈值 "
                    f"{self.config.pipeline.min_confidence:.2f}，跳过执行",
                )

            plan = self.planner.plan(recognition)
            result.plan = plan
            logger.info("计划生成 | intent=%s | params=%s", plan.intent.value, plan.params)

            action_opts = dict(self.config.actions.get(plan.intent.value) or {})
            # save_file 输出目录转为绝对路径
            if "output_dir" in action_opts:
                action_opts["output_dir"] = str(
                    self.config.resolve_path(str(action_opts["output_dir"]))
                )

            action = get_action(
                plan.intent,
                options=action_opts,
                dry_run=self.config.pipeline.dry_run,
            )
            action_result = action.run(plan)
            result.action = action_result
            logger.info(
                "动作完成 | status=%s | message=%s",
                action_result.status.value,
                action_result.message,
            )

            ok = action_result.status in {
                ActionStatus.SUCCESS,
                ActionStatus.DRY_RUN,
                ActionStatus.SKIPPED,
            }
            return result.finish(ok, action_result.message)
        except Exception as exc:  # noqa: BLE001
            logger.exception("流水线失败: %s", exc)
            return result.finish(False, str(exc))
