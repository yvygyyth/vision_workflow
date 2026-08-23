"""识图设置。"""

from __future__ import annotations

from collections.abc import Callable

import customtkinter as ctk

from vision_bot.core.settings import MatchSettings, get_match_settings, save_match_settings
from vision_bot.ui import theme

_FIXED_BASELINE = MatchSettings()


class SettingsDialog(ctk.CTkToplevel):
    def __init__(self, master: ctk.CTk, *, on_saved: Callable[[MatchSettings], None] | None = None) -> None:
        super().__init__(master)
        self.title("识图设置")
        self.geometry("420x380")
        self.resizable(False, False)
        self.configure(fg_color=theme.BG)
        self._on_saved = on_saved
        self.transient(master)
        self.grab_set()

        frame = ctk.CTkFrame(self, fg_color=theme.SURFACE, corner_radius=12)
        frame.pack(fill="both", expand=True, padx=16, pady=16)
        frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(frame, text="识图匹配", font=theme.FONT_TITLE, text_color=theme.TEXT).grid(
            row=0, column=0, columnspan=2, sticky="w", padx=16, pady=(14, 8)
        )
        cfg = get_match_settings()
        self._min_var = ctk.StringVar(value=str(cfg.scale_min))
        self._max_var = ctk.StringVar(value=str(cfg.scale_max))
        self._samples_var = ctk.StringVar(value=str(cfg.scale_samples))
        self._multi_var = ctk.BooleanVar(value=cfg.multi_scale)

        ctk.CTkLabel(frame, text="模板基准分辨率", font=theme.FONT_UI, text_color=theme.TEXT).grid(
            row=1, column=0, sticky="w", padx=(16, 8), pady=8
        )
        ctk.CTkLabel(frame, text=_FIXED_BASELINE.baseline_label(), font=theme.FONT_UI, text_color=theme.MUTED).grid(
            row=1, column=1, sticky="w", padx=(0, 16), pady=8
        )
        self._row(frame, 2, "多尺度下限", self._min_var)
        self._row(frame, 3, "多尺度上限", self._max_var)
        self._row(frame, 4, "分几档", self._samples_var)
        ctk.CTkLabel(frame, text="开启多尺度", font=theme.FONT_UI, text_color=theme.TEXT).grid(
            row=5, column=0, sticky="w", padx=(16, 8), pady=8
        )
        ctk.CTkSwitch(frame, text="", variable=self._multi_var, progress_color=theme.ACCENT).grid(
            row=5, column=1, sticky="w", padx=(0, 16), pady=8
        )
        self._error = ctk.CTkLabel(frame, text="", font=theme.FONT_UI, text_color=theme.ERR)
        self._error.grid(row=6, column=0, columnspan=2, sticky="w", padx=16)

        btns = ctk.CTkFrame(frame, fg_color="transparent")
        btns.grid(row=7, column=0, columnspan=2, sticky="ew", padx=16, pady=(12, 14))
        btns.grid_columnconfigure((0, 1), weight=1)
        ctk.CTkButton(btns, text="取消", command=self.destroy, height=34, font=theme.FONT_UI).grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ctk.CTkButton(btns, text="保存", command=self._save, height=34, fg_color=theme.ACCENT, font=theme.FONT_UI).grid(row=0, column=1, sticky="ew", padx=(6, 0))

    def _row(self, parent, row, label, var) -> None:
        ctk.CTkLabel(parent, text=label, font=theme.FONT_UI, text_color=theme.TEXT).grid(row=row, column=0, sticky="w", padx=(16, 8), pady=8)
        ctk.CTkEntry(parent, textvariable=var, font=theme.FONT_UI, height=34).grid(row=row, column=1, sticky="ew", padx=(0, 16), pady=8)

    def _save(self) -> None:
        try:
            settings = MatchSettings(
                baseline_width=_FIXED_BASELINE.baseline_width,
                baseline_height=_FIXED_BASELINE.baseline_height,
                scale_min=float(self._min_var.get()),
                scale_max=float(self._max_var.get()),
                scale_samples=int(self._samples_var.get()),
                multi_scale=bool(self._multi_var.get()),
            ).validate()
        except Exception as exc:  # noqa: BLE001
            self._error.configure(text=str(exc))
            return
        if self._on_saved:
            self._on_saved(save_match_settings(settings))
        self.destroy()
