"""识图设置弹窗。"""

from __future__ import annotations

from collections.abc import Callable

import customtkinter as ctk

from vision_workflow.settings import MatchSettings, get_match_settings, save_match_settings
from vision_workflow.ui import theme


class SettingsDialog(ctk.CTkToplevel):
    """模块化设置页：基准分辨率 / 多尺度上下限 / 是否开启多尺度。"""

    def __init__(
        self,
        master: ctk.CTk,
        *,
        on_saved: Callable[[MatchSettings], None] | None = None,
    ) -> None:
        super().__init__(master)
        self.title("识图设置")
        self.geometry("420x360")
        self.resizable(False, False)
        self.configure(fg_color=theme.BG)
        self._on_saved = on_saved

        self.transient(master)
        self.grab_set()

        frame = ctk.CTkFrame(self, fg_color=theme.SURFACE, corner_radius=12)
        frame.pack(fill="both", expand=True, padx=16, pady=16)
        frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            frame,
            text="识图匹配",
            font=theme.FONT_TITLE,
            text_color=theme.TEXT,
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=16, pady=(14, 8))

        cfg = get_match_settings()

        self._baseline_var = ctk.StringVar(value=cfg.baseline_label())
        self._min_var = ctk.StringVar(value=str(cfg.scale_min))
        self._max_var = ctk.StringVar(value=str(cfg.scale_max))
        self._multi_var = ctk.BooleanVar(value=cfg.multi_scale)

        self._add_row(frame, 1, "模板基准分辨率", self._baseline_var, hint="如 2560x1440")
        self._add_row(frame, 2, "多尺度下限", self._min_var, hint="相对基准换算，如 0.9")
        self._add_row(frame, 3, "多尺度上限", self._max_var, hint="相对基准换算，如 1.1")

        ctk.CTkLabel(frame, text="开启多尺度", font=theme.FONT_UI, text_color=theme.TEXT).grid(
            row=4, column=0, sticky="w", padx=(16, 8), pady=8
        )
        self._multi_switch = ctk.CTkSwitch(
            frame,
            text="",
            variable=self._multi_var,
            onvalue=True,
            offvalue=False,
            progress_color=theme.ACCENT,
        )
        self._multi_switch.grid(row=4, column=1, sticky="w", padx=(0, 16), pady=8)

        self._error = ctk.CTkLabel(frame, text="", font=theme.FONT_UI, text_color=theme.ERR)
        self._error.grid(row=5, column=0, columnspan=2, sticky="w", padx=16, pady=(4, 0))

        btns = ctk.CTkFrame(frame, fg_color="transparent")
        btns.grid(row=6, column=0, columnspan=2, sticky="ew", padx=16, pady=(12, 14))
        btns.grid_columnconfigure(0, weight=1)
        btns.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(
            btns,
            text="取消",
            command=self.destroy,
            height=34,
            fg_color="#EEF1EF",
            hover_color="#E2E7E4",
            text_color=theme.MUTED,
            font=theme.FONT_UI,
        ).grid(row=0, column=0, sticky="ew", padx=(0, 6))

        ctk.CTkButton(
            btns,
            text="保存",
            command=self._save,
            height=34,
            fg_color=theme.ACCENT,
            hover_color="#255A3F",
            font=theme.FONT_UI,
        ).grid(row=0, column=1, sticky="ew", padx=(6, 0))

        self.after(50, self._focus)

    def _focus(self) -> None:
        self.lift()
        self.focus_force()

    def _add_row(
        self,
        parent: ctk.CTkFrame,
        row: int,
        label: str,
        variable: ctk.StringVar,
        *,
        hint: str,
    ) -> None:
        ctk.CTkLabel(parent, text=label, font=theme.FONT_UI, text_color=theme.TEXT).grid(
            row=row, column=0, sticky="w", padx=(16, 8), pady=8
        )
        entry = ctk.CTkEntry(
            parent,
            textvariable=variable,
            font=theme.FONT_UI,
            height=34,
            placeholder_text=hint,
        )
        entry.grid(row=row, column=1, sticky="ew", padx=(0, 16), pady=8)

    def _save(self) -> None:
        try:
            w, h = _parse_resolution(self._baseline_var.get())
            settings = MatchSettings(
                baseline_width=w,
                baseline_height=h,
                scale_min=float(self._min_var.get().strip()),
                scale_max=float(self._max_var.get().strip()),
                multi_scale=bool(self._multi_var.get()),
            ).validate()
        except Exception as exc:  # noqa: BLE001
            self._error.configure(text=str(exc))
            return

        saved = save_match_settings(settings)
        if self._on_saved:
            self._on_saved(saved)
        self.destroy()


def _parse_resolution(text: str) -> tuple[int, int]:
    raw = text.strip().lower().replace("×", "x").replace("*", "x")
    if "x" not in raw:
        raise ValueError("基准分辨率格式应为 宽x高，如 2560x1440")
    a, b = raw.split("x", 1)
    w, h = int(a.strip()), int(b.strip())
    if w <= 0 or h <= 0:
        raise ValueError("分辨率宽高必须为正整数")
    return w, h
