"""后台运行 start(job_id)。"""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from dataclasses import dataclass

from vision_bot.jobs import start
from vision_bot.logging_utils import setup_logging
from vision_bot.runtime.runner import RunReport

logger = logging.getLogger(__name__)


@dataclass
class RunRequest:
    job_id: str


class JobWorker:
    def __init__(self, *, on_finished: Callable[[RunReport | None, BaseException | None], None]) -> None:
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
        self._thread = threading.Thread(target=self._run, args=(request,), name="job-worker", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._cancel.set()
        logger.info("已请求停止，等待当前步骤退出…")

    def _run(self, request: RunRequest) -> None:
        report: RunReport | None = None
        error: BaseException | None = None
        try:
            setup_logging(gui=True)
            logger.info("启动任务 %s", request.job_id)
            report = start(request.job_id, cancel_event=self._cancel)
        except BaseException as exc:
            error = exc
            logger.exception("执行失败")
        self._on_finished(report, error)
