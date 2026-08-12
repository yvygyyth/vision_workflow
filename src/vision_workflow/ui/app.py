"""启动桌面 UI。"""

from __future__ import annotations

import customtkinter as ctk

from vision_workflow.config import reload_settings
from vision_workflow.logging_utils import setup_logging
from vision_workflow.ui import theme
from vision_workflow.ui.window import MainWindow


def run_app() -> None:
    setup_logging(reload_settings(), gui=True)

    ctk.set_appearance_mode(theme.APPEARANCE)
    ctk.set_default_color_theme(theme.COLOR_THEME)

    app = MainWindow()
    app.mainloop()
