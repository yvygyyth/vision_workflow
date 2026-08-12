"""后台线程执行 Workflow，避免卡住 UI。"""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from dataclasses import dataclass

from vision_workflow.config import reload_settings
from vision_workflow.flow import FlowRunner, load_flow_module
from vision_workflow.logging_utils import setup_logging
from vision_workflow.models.flow import FlowRunResult
from vision_workflow.paths import ensure_runtime_path, project_root

logger = logging.getLogger(__name__)


@dataclass
class RunRequest:
    target: str
    dry_run: bool
    start: str | None = None


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
            root = ensure_runtime_path()
            setup_logging(reload_settings(), gui=True)
            workflow = load_flow_module(request.target)
            if workflow.base_dir is None:
                workflow.base_dir = str(root)
            runner = FlowRunner(
                workflow,
                base_dir=project_root(),
                dry_run=request.dry_run,
                cancel_event=self._cancel,
            )
            mode = "dry-run" if request.dry_run else "live"
            logger.info("开始执行 target=%s mode=%s", request.target, mode)
            result = runner.run(start=request.start or None)
        except BaseException as exc:  # noqa: BLE001
            error = exc
            logger.exception("执行失败: %s", exc)
        self._on_finished(result, error)
