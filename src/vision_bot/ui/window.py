"""主窗口。"""

from __future__ import annotations

import logging
import queue

import customtkinter as ctk

from vision_bot.core.settings import MatchSettings
from vision_bot.logging_utils import setup_logging
from vision_bot.runtime.catalog import DEFAULT_ROOT_ID, root_flow_choices
from vision_bot.runtime.runner import RunReport
from vision_bot.ui import theme
from vision_bot.ui.panels.flow_run_panel import FlowRunPanel
from vision_bot.ui.panels.log_panel import LogPanel
from vision_bot.ui.panels.settings_dialog import SettingsDialog
from vision_bot.ui.panels.status_bar import StatusBar
from vision_bot.ui.services.flow_worker import FlowWorker
from vision_bot.ui.services.hotkeys import TOGGLE_LABEL, GlobalHotkeys
from vision_bot.ui.services.log_bridge import attach_queue_handler, drain_queue

logger = logging.getLogger(__name__)


class MainWindow(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Vision Bot")
        self.geometry("880x720")
        self.minsize(720, 520)
        self.configure(fg_color=theme.BG)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._log_queue: queue.Queue[str] = queue.Queue()
        self._log_handler = attach_queue_handler(self._log_queue)
        self._pending: tuple[RunReport | None, BaseException | None] | None = None

        self.controls = FlowRunPanel(
            self, on_run=self._start, on_stop=self._stop, on_clear=self.logs_clear, on_settings=self._settings
        )
        self.controls.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))
        self.logs = LogPanel(self)
        self.logs.grid(row=1, column=0, sticky="nsew", padx=16, pady=8)
        self.status = StatusBar(self)
        self.status.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 12))

        self.worker = FlowWorker(on_finished=self._on_done)
        self._hotkeys = GlobalHotkeys(on_toggle=self._toggle, schedule=lambda fn: self.after(0, fn))
        self._hotkeys.start()

        self.protocol("WM_DELETE_WINDOW", self._close)
        self.after(80, self._pump)
        self.after(100, self._load_flows)
        setup_logging(gui=True)

    def _load_flows(self) -> None:
        try:
            choices = root_flow_choices()
        except Exception as exc:  # noqa: BLE001
            self.controls.set_root_choices([])
            self.status.set_status(f"加载失败: {exc}", ok=False)
            return
        self.controls.set_root_choices(choices, selected_id=DEFAULT_ROOT_ID)
        self.status.set_status(f"已加载 {len(choices)} 个根 Flow")
        self.logs.append(f"全局快捷键：{TOGGLE_LABEL} = 运行/停止")

    def logs_clear(self) -> None:
        self.logs.clear()

    def _settings(self) -> None:
        if self.worker.busy:
            return
        SettingsDialog(self, on_saved=self._on_settings_saved)

    def _on_settings_saved(self, s: MatchSettings) -> None:
        self.logs.append(f"已保存识图设置 baseline={s.baseline_label()}")
        self.status.set_status("设置已保存")

    def _toggle(self) -> None:
        self._stop() if self.worker.busy else self._start()

    def _start(self) -> None:
        if self.worker.busy:
            return
        request, err = self.controls.prepare_run()
        self.controls.params_hint.configure(text=err)
        if request is None:
            self.status.set_status(err, ok=False)
            return
        label = self.controls.selected_label()
        self.status.set_status(f"运行中：{label}")
        self.logs.append(f"—— 开始：{label}（{request.entry_id}）——")
        try:
            self.worker.start(request)
            self.controls.set_locked(True)
        except Exception as exc:  # noqa: BLE001
            self.controls.set_locked(False)
            self.status.set_status(str(exc), ok=False)

    def _stop(self) -> None:
        if self.worker.busy:
            self.worker.stop()
            self.logs.append("—— 请求停止 ——")

    def _on_done(self, result: RunReport | None, error: BaseException | None) -> None:
        self._pending = (result, error)

    def _pump(self) -> None:
        drain_queue(self._log_queue, self.logs.append)
        if self._pending is not None:
            result, error = self._pending
            self._pending = None
            self.controls.set_locked(False)
            if error:
                self.status.set_status(str(error), ok=False)
            elif result:
                path = " → ".join(result.path) if result.path else ""
                self.logs.append(f"结果 {'成功' if result.success else '失败'} | {result.message}")
                if path:
                    self.logs.append(f"路径: {path}")
                self.status.set_status(result.message or "完成", ok=result.success)
        self.after(80, self._pump)

    def _close(self) -> None:
        self._hotkeys.stop()
        if self.worker.busy:
            self.worker.stop()
        logging.getLogger().removeHandler(self._log_handler)
        self.destroy()
