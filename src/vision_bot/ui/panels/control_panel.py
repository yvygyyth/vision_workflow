"""运行 / 停止。"""

from __future__ import annotations

from collections.abc import Callable

import customtkinter as ctk

from vision_bot.ui import theme
from vision_bot.ui.services.hotkeys import TOGGLE_LABEL


class ControlPanel(ctk.CTkFrame):
    def __init__(
        self,
        master: ctk.CTk | ctk.CTkFrame,
        *,
        on_run: Callable[[], None],
        on_stop: Callable[[], None],
        on_clear: Callable[[], None],
        on_settings: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(master, fg_color=theme.SURFACE, corner_radius=12)
        self.grid_columnconfigure(1, weight=1)

        self._job_by_label: dict[str, str] = {}

        ctk.CTkLabel(self, text="Vision Bot", font=theme.FONT_TITLE, text_color=theme.TEXT).grid(
            row=0, column=0, columnspan=5, sticky="w", padx=16, pady=(14, 4)
        )
        ctk.CTkLabel(
            self,
            text=f"选择任务后运行 · {TOGGLE_LABEL} 运行/停止",
            font=theme.FONT_UI,
            text_color=theme.MUTED,
        ).grid(row=1, column=0, columnspan=5, sticky="w", padx=16, pady=(0, 10))

        ctk.CTkLabel(self, text="任务", font=theme.FONT_UI, text_color=theme.TEXT).grid(
            row=2, column=0, sticky="w", padx=(16, 8), pady=6
        )
        self.job_var = ctk.StringVar(value="")
        self.job_menu = ctk.CTkOptionMenu(
            self,
            variable=self.job_var,
            values=["(未加载)"],
            font=theme.FONT_UI,
            height=34,
            fg_color="#E7EEE9",
            button_color=theme.ACCENT,
            button_hover_color="#255A3F",
            text_color=theme.TEXT,
        )
        self.job_menu.grid(row=2, column=1, columnspan=4, sticky="ew", padx=(0, 16), pady=6)

        self.btn_run = ctk.CTkButton(
            self, text=f"运行 ({TOGGLE_LABEL})", command=on_run, height=36,
            fg_color=theme.ACCENT, hover_color="#255A3F", font=theme.FONT_UI,
        )
        self.btn_run.grid(row=3, column=0, columnspan=2, sticky="ew", padx=(16, 8), pady=(8, 14))

        self.btn_stop = ctk.CTkButton(
            self, text=f"停止 ({TOGGLE_LABEL})", command=on_stop, height=36,
            fg_color="#F3E8E6", hover_color="#E9D5D1", text_color=theme.ERR,
            font=theme.FONT_UI, state="disabled",
        )
        self.btn_stop.grid(row=3, column=2, sticky="ew", padx=8, pady=(8, 14))

        self.btn_clear = ctk.CTkButton(
            self, text="清日志", command=on_clear, height=36,
            fg_color="#EEF1EF", hover_color="#E2E7E4", text_color=theme.MUTED, font=theme.FONT_UI,
        )
        self.btn_clear.grid(row=3, column=3, sticky="ew", padx=8, pady=(8, 14))

        self.btn_settings = ctk.CTkButton(
            self, text="设置", command=on_settings or (lambda: None), height=36,
            fg_color="#EEF1EF", hover_color="#E2E7E4", text_color=theme.TEXT, font=theme.FONT_UI,
            state="normal" if on_settings else "disabled",
        )
        self.btn_settings.grid(row=3, column=4, sticky="ew", padx=(8, 16), pady=(8, 14))

    def selected_job_id(self) -> str | None:
        return self._job_by_label.get(self.job_var.get().strip())

    def selected_job_name(self) -> str:
        return self.job_var.get().strip()

    def set_job_choices(self, choices: list[tuple[str, str]], *, selected_id: str | None = None) -> None:
        self._job_by_label = {label: jid for label, jid in choices}
        labels = [label for label, _ in choices] or ["(无任务)"]
        self.job_menu.configure(values=labels)
        pick = labels[0]
        if selected_id:
            for label, jid in choices:
                if jid == selected_id:
                    pick = label
                    break
        self.job_var.set(pick)

    def set_running(self, running: bool) -> None:
        self.btn_run.configure(state="disabled" if running else "normal")
        self.btn_stop.configure(state="normal" if running else "disabled")
        self.job_menu.configure(state="disabled" if running else "normal")
        self.btn_settings.configure(state="disabled" if running else "normal")
