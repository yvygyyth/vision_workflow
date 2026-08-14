"""控制区：复杂流程选择、运行/停止。"""

from __future__ import annotations

from collections.abc import Callable

import customtkinter as ctk

from vision_workflow.ui import theme


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

        self._workflow_by_label: dict[str, str] = {}
        self._on_settings = on_settings

        self.title_label = ctk.CTkLabel(
            self,
            text="Vision Workflow",
            font=theme.FONT_TITLE,
            text_color=theme.TEXT,
        )
        self.title_label.grid(row=0, column=0, columnspan=5, sticky="w", padx=16, pady=(14, 4))

        self.subtitle_label = ctk.CTkLabel(
            self,
            text="选择复杂流程后运行",
            font=theme.FONT_UI,
            text_color=theme.MUTED,
        )
        self.subtitle_label.grid(row=1, column=0, columnspan=5, sticky="w", padx=16, pady=(0, 10))

        ctk.CTkLabel(self, text="复杂流程", font=theme.FONT_UI, text_color=theme.TEXT).grid(
            row=2, column=0, sticky="w", padx=(16, 8), pady=6
        )
        self.workflow_var = ctk.StringVar(value="")
        self.workflow_menu = ctk.CTkOptionMenu(
            self,
            variable=self.workflow_var,
            values=["(未加载)"],
            font=theme.FONT_UI,
            height=34,
            fg_color="#E7EEE9",
            button_color=theme.ACCENT,
            button_hover_color="#255A3F",
            text_color=theme.TEXT,
        )
        self.workflow_menu.grid(row=2, column=1, columnspan=4, sticky="ew", padx=(0, 16), pady=6)

        self.btn_run = ctk.CTkButton(
            self,
            text="运行",
            command=on_run,
            height=36,
            fg_color=theme.ACCENT,
            hover_color="#255A3F",
            font=theme.FONT_UI,
        )
        self.btn_run.grid(row=3, column=0, columnspan=2, sticky="ew", padx=(16, 8), pady=(8, 14))

        self.btn_stop = ctk.CTkButton(
            self,
            text="停止",
            command=on_stop,
            height=36,
            fg_color="#F3E8E6",
            hover_color="#E9D5D1",
            text_color=theme.ERR,
            font=theme.FONT_UI,
            state="disabled",
        )
        self.btn_stop.grid(row=3, column=2, sticky="ew", padx=8, pady=(8, 14))

        self.btn_clear = ctk.CTkButton(
            self,
            text="清日志",
            command=on_clear,
            height=36,
            fg_color="#EEF1EF",
            hover_color="#E2E7E4",
            text_color=theme.MUTED,
            font=theme.FONT_UI,
        )
        self.btn_clear.grid(row=3, column=3, sticky="ew", padx=8, pady=(8, 14))

        self.btn_settings = ctk.CTkButton(
            self,
            text="设置",
            command=self._on_settings or (lambda: None),
            height=36,
            fg_color="#EEF1EF",
            hover_color="#E2E7E4",
            text_color=theme.TEXT,
            font=theme.FONT_UI,
            state="normal" if on_settings else "disabled",
        )
        self.btn_settings.grid(row=3, column=4, sticky="ew", padx=(8, 16), pady=(8, 14))

    def selected_workflow_id(self) -> str | None:
        label = self.workflow_var.get().strip()
        return self._workflow_by_label.get(label)

    def selected_workflow_name(self) -> str:
        return self.workflow_var.get().strip()

    def set_workflow_choices(
        self,
        choices: list[tuple[str, str]],
        *,
        selected_id: str | None = None,
    ) -> None:
        """choices: (display_name, workflow_id)。"""
        self._workflow_by_label = {label: wid for label, wid in choices}
        labels = [label for label, _ in choices] or ["(无复杂流程)"]
        self.workflow_menu.configure(values=labels)

        selected_label = labels[0]
        if selected_id:
            for label, wid in choices:
                if wid == selected_id:
                    selected_label = label
                    break
        self.workflow_var.set(selected_label)

    def set_running(self, running: bool) -> None:
        state_run = "disabled" if running else "normal"
        state_stop = "normal" if running else "disabled"
        self.btn_run.configure(state=state_run)
        self.btn_stop.configure(state=state_stop)
        self.workflow_menu.configure(state="disabled" if running else "normal")
        if self._on_settings:
            self.btn_settings.configure(state="disabled" if running else "normal")
