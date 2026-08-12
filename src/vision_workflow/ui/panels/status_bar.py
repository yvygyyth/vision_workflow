"""底部状态条。"""

from __future__ import annotations

import customtkinter as ctk

from vision_workflow.ui import theme


class StatusBar(ctk.CTkFrame):
    def __init__(self, master: ctk.CTk | ctk.CTkFrame) -> None:
        super().__init__(master, fg_color="transparent", height=28)
        self.label = ctk.CTkLabel(
            self,
            text="就绪",
            font=theme.FONT_UI,
            text_color=theme.MUTED,
            anchor="w",
        )
        self.label.pack(fill="x", padx=4)

    def set_status(self, text: str, *, ok: bool | None = None) -> None:
        color = theme.MUTED
        if ok is True:
            color = theme.OK
        elif ok is False:
            color = theme.ERR
        self.label.configure(text=text, text_color=color)
