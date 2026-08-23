"""状态条。"""

import customtkinter as ctk

from vision_bot.ui import theme


class StatusBar(ctk.CTkFrame):
    def __init__(self, master) -> None:
        super().__init__(master, fg_color="transparent", height=28)
        self.label = ctk.CTkLabel(self, text="就绪", font=theme.FONT_UI, text_color=theme.MUTED, anchor="w")
        self.label.pack(fill="x", padx=4)

    def set_status(self, text: str, *, ok: bool | None = None) -> None:
        color = theme.MUTED if ok is None else (theme.OK if ok else theme.ERR)
        self.label.configure(text=text, text_color=color)
