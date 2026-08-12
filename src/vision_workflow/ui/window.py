"""主窗口：组装控制区 / 日志 / 状态条。"""

from __future__ import annotations

import logging
import queue

import customtkinter as ctk

from vision_workflow.flow import load_flow_module
from vision_workflow.models.flow import FlowRunResult
from vision_workflow.paths import ensure_runtime_path
from vision_workflow.ui import theme
from vision_workflow.ui.panels.control_panel import ControlPanel
from vision_workflow.ui.panels.log_panel import LogPanel
from vision_workflow.ui.panels.status_bar import StatusBar
from vision_workflow.ui.services.log_bridge import attach_queue_handler, drain_queue
from vision_workflow.ui.services.workflow_worker import RunRequest, WorkflowWorker

logger = logging.getLogger(__name__)


class MainWindow(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Vision Workflow")
        self.geometry("880x640")
        self.minsize(720, 480)
        self.configure(fg_color=theme.BG)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._log_queue: queue.Queue[str] = queue.Queue()
        self._log_handler = attach_queue_handler(self._log_queue)
        self._pending_finish: tuple[FlowRunResult | None, BaseException | None] | None = None

        self.controls = ControlPanel(
            self,
            on_run=self._start,
            on_stop=self._stop,
            on_clear=self._clear_log,
            on_reload=self._reload_flows,
        )
        self.controls.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))

        self.logs = LogPanel(self)
        self.logs.grid(row=1, column=0, sticky="nsew", padx=16, pady=8)

        self.status = StatusBar(self)
        self.status.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 12))

        self.worker = WorkflowWorker(on_finished=self._on_worker_finished)

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(80, self._pump)
        self.after(100, self._reload_flows)

    def _reload_flows(self) -> None:
        ensure_runtime_path()
        target = self.controls.target()
        try:
            workflow = load_flow_module(target)
        except Exception as exc:  # noqa: BLE001
            self.controls.set_workflow_meta("Vision Workflow")
            self.controls.set_flow_choices([])
            self.status.set_status(f"加载失败: {exc}", ok=False)
            self.logs.append(f"加载 {target} 失败: {exc}")
            return

        self.title(f"Vision Workflow · {workflow.display_name}")
        self.controls.set_workflow_meta(workflow.display_name)
        self.controls.set_flow_choices(workflow.flow_choices(), selected_id=workflow.entry)
        self.status.set_status(f"已加载：{workflow.display_name}")
        self.logs.append(
            f"已加载工作流 [{workflow.display_name}]，共 {len(workflow.flows)} 个流程"
        )

    def _start(self) -> None:
        if self.worker.busy:
            self.status.set_status("已有任务在运行", ok=False)
            return
        target = self.controls.target()
        flow_id = self.controls.selected_flow_id()
        flow_name = self.controls.selected_flow_name() or flow_id or "入口"
        if not flow_id:
            self.status.set_status("请先刷新并选择流程", ok=False)
            return

        self.controls.set_running(True)
        self.status.set_status(f"运行中：{flow_name}")
        self.logs.append(f"—— 开始运行：{flow_name}（{target} / {flow_id}）——")
        try:
            self.worker.start(RunRequest(target=target, start=flow_id))
        except Exception as exc:  # noqa: BLE001
            self.controls.set_running(False)
            self.status.set_status(f"启动失败: {exc}", ok=False)
            self.logs.append(str(exc))

    def _stop(self) -> None:
        if not self.worker.busy:
            return
        self.worker.stop()
        self.status.set_status("正在停止…")
        self.logs.append("—— 请求停止 ——")

    def _clear_log(self) -> None:
        self.logs.clear()

    def _on_worker_finished(
        self,
        result: FlowRunResult | None,
        error: BaseException | None,
    ) -> None:
        self._pending_finish = (result, error)

    def _apply_finish(
        self,
        result: FlowRunResult | None,
        error: BaseException | None,
    ) -> None:
        self.controls.set_running(False)
        if error is not None:
            self.status.set_status(f"异常: {error}", ok=False)
            return
        if result is None:
            self.status.set_status("无结果", ok=False)
            return
        path = " → ".join(result.path) if result.path else "(empty)"
        self.logs.append(
            f"结果 [{result.flow_name}] success={result.success} | {result.feedback or result.message}"
        )
        self.logs.append(f"path: {path}")
        self.status.set_status(
            result.feedback or result.message or ("成功" if result.success else "失败"),
            ok=result.success,
        )

    def _pump(self) -> None:
        drain_queue(self._log_queue, self.logs.append)
        if self._pending_finish is not None:
            result, error = self._pending_finish
            self._pending_finish = None
            self._apply_finish(result, error)
        self.after(80, self._pump)

    def _on_close(self) -> None:
        if self.worker.busy:
            self.worker.stop()
        root = logging.getLogger()
        if self._log_handler in root.handlers:
            root.removeHandler(self._log_handler)
        self.destroy()
