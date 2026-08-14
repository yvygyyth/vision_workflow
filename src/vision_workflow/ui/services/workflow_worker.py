"""后台线程执行 Workflow，避免卡住 UI。"""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from dataclasses import dataclass

from vision_workflow.config import reload_settings
from vision_workflow.flow import WorkflowRunner
from vision_workflow.flows import get_workflow
from vision_workflow.logging_utils import setup_logging
from vision_workflow.models.flow import FlowRunResult
from vision_workflow.paths import project_root

logger = logging.getLogger(__name__)


@dataclass
class RunRequest:
    workflow_id: str


class WorkflowWorker:
    def __init__(
        self,
        *,
        on_finished: Callable[[FlowRunResult | None, BaseException | None], None],
    ) -> None:
        self._on_finished = on_finished
        self._thread: threading.Thread | None = None
        self._cancel = threading.Event()

    @property
    def busy(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self, request: RunRequest) -> None:
        if self.busy:
            raise RuntimeError("已有任务在运行")
        self._cancel.clear()
        self._thread = threading.Thread(
            target=self._run,
            args=(request,),
            name="workflow-worker",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        self._cancel.set()

    def _run(self, request: RunRequest) -> None:
        result: FlowRunResult | None = None
        error: BaseException | None = None
        try:
            setup_logging(reload_settings(), gui=True)
            workflow = get_workflow(request.workflow_id)
            root = project_root()
            if workflow.base_dir is None:
                workflow.base_dir = str(root)
            runner = WorkflowRunner(
                workflow,
                base_dir=root,
                cancel_event=self._cancel,
            )
            logger.info(
                "开始执行 复杂流程=%s 入口=%s",
                workflow.log_label,
                workflow.entry,
            )
            # 始终从复杂流程自身入口开始，不暴露子流程选择
            result = runner.run()
        except BaseException as exc:
            error = exc
            logger.exception("执行失败")
        self._on_finished(result, error)
