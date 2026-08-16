"""主窗口：组装控制区 / 日志 / 状态条。"""

from __future__ import annotations

import logging
import queue

import customtkinter as ctk

from vision_workflow.apps import WORKFLOW, workflow_choices
from vision_workflow.models.flow import FlowRunResult
from vision_workflow.settings import MatchSettings
from vision_workflow.ui import theme
from vision_workflow.ui.panels.control_panel import ControlPanel
from vision_workflow.ui.panels.log_panel import LogPanel
from vision_workflow.ui.panels.settings_dialog import SettingsDialog
from vision_workflow.ui.panels.status_bar import StatusBar
from vision_workflow.ui.services.hotkeys import TOGGLE_LABEL, GlobalHotkeys
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
            on_settings=self._open_settings,
        )
        self.controls.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))

        self.logs = LogPanel(self)
        self.logs.grid(row=1, column=0, sticky="nsew", padx=16, pady=8)

        self.status = StatusBar(self)
        self.status.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 12))

        self.worker = WorkflowWorker(on_finished=self._on_worker_finished)
        self._hotkeys = GlobalHotkeys(
            on_toggle=self._toggle_run,
            schedule=lambda fn: self.after(0, fn),
        )
        self._hotkeys.start()

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(80, self._pump)
        self.after(100, self._load_catalog)

    def _load_catalog(self) -> None:
        try:
            choices = workflow_choices()
        except Exception as exc:  # noqa: BLE001
            self.controls.set_workflow_choices([])
            self.status.set_status(f"加载失败: {exc}", ok=False)
            self.logs.append(f"加载复杂流程目录失败: {exc}")
            return

        self.controls.set_workflow_choices(choices, selected_id=WORKFLOW.id)
        self.status.set_status(f"已加载 {len(choices)} 个复杂流程")
        self.logs.append(f"已加载复杂流程目录，共 {len(choices)} 项")
        self.logs.append(f"全局快捷键：{TOGGLE_LABEL} = 运行/停止（游戏前台也可用）")
        self._log_match_settings()

    def _log_match_settings(self) -> None:
        try:
            from vision_workflow.display import (
                active_baseline,
                get_display_info,
                match_scales,
                template_scale,
            )
            from vision_workflow.settings import get_match_settings

            cfg = get_match_settings()
            d = get_display_info()
            scale = template_scale(d)
            scales = match_scales(scale)
            self.logs.append(active_baseline().format_line(prefix="模板基准"))
            self.logs.append(d.format_line(prefix="当前设备"))
            multi = "开" if cfg.multi_scale else "关"
            self.logs.append(
                f"识图设置 baseline={cfg.baseline_label()} "
                f"multi={multi} [{cfg.scale_min:g},{cfg.scale_max:g}] "
                f"samples={cfg.scale_samples} "
                f"base={scale:.4f} → {[round(s, 4) for s in scales]}"
            )
        except Exception as exc:  # noqa: BLE001
            self.logs.append(f"显示参数读取失败: {exc}")

    def _open_settings(self) -> None:
        if self.worker.busy:
            self.status.set_status("运行中不可改设置", ok=False)
            return
        SettingsDialog(self, on_saved=self._on_settings_saved)

    def _on_settings_saved(self, settings: MatchSettings) -> None:
        multi = "开" if settings.multi_scale else "关"
        self.logs.append(
            f"已保存识图设置 baseline={settings.baseline_label()} "
            f"multi={multi} [{settings.scale_min:g},{settings.scale_max:g}] "
            f"samples={settings.scale_samples}"
        )
        self._log_match_settings()
        self.status.set_status("设置已保存")

    def _toggle_run(self) -> None:
        if self.worker.busy:
            self._stop()
        else:
            self._start()

    def _start(self) -> None:
        if self.worker.busy:
            self.status.set_status("已有任务在运行", ok=False)
            return
        workflow_id = self.controls.selected_workflow_id()
        workflow_name = self.controls.selected_workflow_name() or workflow_id or "复杂流程"
        if not workflow_id:
            self.status.set_status("请先选择复杂流程", ok=False)
            return

        self.controls.set_running(True)
        self.status.set_status(f"运行中：{workflow_name}")
        self.logs.append(f"—— 开始运行：{workflow_name}（{workflow_id}）——")
        try:
            self.worker.start(RunRequest(workflow_id=workflow_id))
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
        path_labels = [
            s.step_label or s.step_id for s in result.steps if s.step_label or s.step_id
        ]
        path = " → ".join(path_labels) if path_labels else "(empty)"
        ok_text = "成功" if result.success else "失败"
        self.logs.append(
            f"结果 [{result.flow_name}] {ok_text} | {result.feedback or result.message}"
        )
        self.logs.append(f"路径: {path}")
        self.status.set_status(
            result.feedback or result.message or ok_text,
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
        self._hotkeys.stop()
        if self.worker.busy:
            self.worker.stop()
        root = logging.getLogger()
        if self._log_handler in root.handlers:
            root.removeHandler(self._log_handler)
        self.destroy()
