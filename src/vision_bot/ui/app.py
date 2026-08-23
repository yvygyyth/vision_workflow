"""桌面 UI。"""

import customtkinter as ctk

from vision_bot.ui import theme
from vision_bot.ui.window import MainWindow


def run_app() -> None:
    ctk.set_appearance_mode(theme.APPEARANCE)
    ctk.set_default_color_theme(theme.COLOR_THEME)
    MainWindow().mainloop()
