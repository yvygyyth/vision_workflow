"""控制区：目标、干跑/运行/停止。"""

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
        on_dry_run: Callable[[], None],
        on_stop: Callable[[], None],
        on_clear: Callable[[], None],
        default_target: str = "config.flow",
    ) -> None:
        super().__init__(master, fg_color=theme.SURFACE, corner_radius=12)
        self.grid_columnconfigure(1, weight=1)

        title = ctk.CTkLabel(self, text="Vision Workflow", font=theme.FONT_TITLE, text_color=theme.TEXT)
        title.grid(row=0, column=0, columnspan=4, sticky="w", padx=16, pady=(14, 4))

        hint = ctk.CTkLabel(
            self,
            text="模块 → 流程 → 工作流",
            font=theme.FONT_UI,
            text_color=theme.MUTED,
        )
        hint.grid(row=1, column=0, columnspan=4, sticky="w", padx=16, pady=(0, 10))

        ctk.CTkLabel(self, text="流程", font=theme.FONT_UI, text_color=theme.TEXT).grid(
            row=2, column=0, sticky="w", padx=(16, 8), pady=8
        )
        self.target_var = ctk.StringVar(value=default_target)
        self.target_entry = ctk.CTkEntry(
            self,
            textvariable=self.target_var,
            font=theme.FONT_UI,
            height=36,
        )
        self.target_entry.grid(row=2, column=1, columnspan=3, sticky="ew", padx=(0, 16), pady=8)

        self.btn_dry = ctk.CTkButton(
            self,
            text="干跑",
            command=on_dry_run,
            height=36,
            fg_color="#E7EEE9",
            hover_color="#D7E3DB",
            text_color=theme.ACCENT,
            font=theme.FONT_UI,
        )
        self.btn_dry.grid(row=3, column=0, sticky="ew", padx=(16, 8), pady=(4, 14))

        self.btn_run = ctk.CTkButton(
            self,
            text="运行",
            command=on_run,
            height=36,
            fg_color=theme.ACCENT,
            hover_color="#255A3F",
            font=theme.FONT_UI,
        )
        self.btn_run.grid(row=3, column=1, sticky="ew", padx=8, pady=(4, 14))

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
        self.btn_stop.grid(row=3, column=2, sticky="ew", padx=8, pady=(4, 14))

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
        self.btn_clear.grid(row=3, column=3, sticky="ew", padx=(8, 16), pady=(4, 14))

    def target(self) -> str:
        return self.target_var.get().strip() or "config.flow"

    def set_running(self, running: bool) -> None:
        state_run = "disabled" if running else "normal"
        state_stop = "normal" if running else "disabled"
        self.btn_run.configure(state=state_run)
        self.btn_dry.configure(state=state_run)
        self.btn_stop.configure(state=state_stop)
        self.target_entry.configure(state="disabled" if running else "normal")
