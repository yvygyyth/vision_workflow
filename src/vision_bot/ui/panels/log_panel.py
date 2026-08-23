"""日志面板。"""

import customtkinter as ctk

from vision_bot.ui import theme


class LogPanel(ctk.CTkFrame):
    def __init__(self, master) -> None:
        super().__init__(master, fg_color=theme.SURFACE, corner_radius=12)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self, text="运行日志", font=theme.FONT_UI, text_color=theme.MUTED).grid(
            row=0, column=0, sticky="w", padx=16, pady=(12, 4)
        )
        self.text = ctk.CTkTextbox(self, font=theme.FONT_LOG, fg_color="#F7F9F7", text_color=theme.TEXT, wrap="word")
        self.text.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))
        self.text.configure(state="disabled")

    def append(self, line: str) -> None:
        self.text.configure(state="normal")
        self.text.insert("end", line.rstrip() + "\n")
        self.text.see("end")
        self.text.configure(state="disabled")

    def clear(self) -> None:
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.configure(state="disabled")
