"""Flow 树选择 + 运行配置。"""

from __future__ import annotations

import json
from collections.abc import Callable

import customtkinter as ctk
from tkinter import ttk

from vision_bot.runtime.catalog import get_root_flow
from vision_bot.runtime.flow import Flow
from vision_bot.runtime.registry import FlowRegistry
from vision_bot.runtime.tree import TreeNode, walk_tree
from vision_bot.ui import theme
from vision_bot.ui.services.flow_worker import RunRequest


class FlowRunPanel(ctk.CTkFrame):
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
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._root_by_label: dict[str, str] = {}
        self._tree_nodes: dict[str, str] = {}
        self._registry: FlowRegistry | None = None
        self._locked = False

        ctk.CTkLabel(self, text="Vision Bot", font=theme.FONT_TITLE, text_color=theme.TEXT).grid(
            row=0, column=0, sticky="w", padx=16, pady=(14, 4)
        )

        row1 = ctk.CTkFrame(self, fg_color="transparent")
        row1.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 6))
        row1.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(row1, text="根 Flow", font=theme.FONT_UI, text_color=theme.TEXT).grid(
            row=0, column=0, sticky="w", padx=(0, 8)
        )
        self.root_var = ctk.StringVar(value="")
        self.root_menu = ctk.CTkOptionMenu(
            row1,
            variable=self.root_var,
            values=["(未加载)"],
            command=self._on_root_changed,
            font=theme.FONT_UI,
            height=34,
            fg_color="#E7EEE9",
            button_color=theme.ACCENT,
            button_hover_color="#255A3F",
            text_color=theme.TEXT,
        )
        self.root_menu.grid(row=0, column=1, sticky="ew")

        tree_wrap = ctk.CTkFrame(self, fg_color="#F4F7F5", corner_radius=8)
        tree_wrap.grid(row=2, column=0, sticky="nsew", padx=16, pady=6)
        tree_wrap.grid_columnconfigure(0, weight=1)
        tree_wrap.grid_rowconfigure(0, weight=1)

        self._tree = ttk.Treeview(tree_wrap, show="tree", selectmode="browse")
        self._tree.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        scroll = ttk.Scrollbar(tree_wrap, orient="vertical", command=self._tree.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        self._tree.configure(yscrollcommand=scroll.set)
        self._tree.bind("<<TreeviewSelect>>", self._on_tree_select)

        cfg = ctk.CTkFrame(self, fg_color="transparent")
        cfg.grid(row=3, column=0, sticky="ew", padx=16, pady=4)
        cfg.grid_columnconfigure(0, weight=1)

        self.loop_var = ctk.BooleanVar(value=False)
        self.loop_cb = ctk.CTkCheckBox(cfg, text="循环 (loop)", variable=self.loop_var, font=theme.FONT_UI)
        self.loop_cb.grid(row=0, column=0, sticky="w", pady=(0, 4))

        ctk.CTkLabel(cfg, text="params (JSON)", font=theme.FONT_UI, text_color=theme.MUTED).grid(
            row=1, column=0, sticky="w"
        )
        self.params_box = ctk.CTkTextbox(cfg, height=72, font=theme.FONT_UI)
        self.params_box.grid(row=2, column=0, sticky="ew", pady=(2, 0))
        self.params_box.insert("1.0", "{}")
        self.params_hint = ctk.CTkLabel(cfg, text="", font=theme.FONT_UI, text_color=theme.ERR)
        self.params_hint.grid(row=3, column=0, sticky="w")

        btn = ctk.CTkFrame(self, fg_color="transparent")
        btn.grid(row=4, column=0, sticky="ew", padx=16, pady=(8, 14))
        btn.grid_columnconfigure((0, 1, 2, 3), weight=1)

        from vision_bot.ui.services.hotkeys import TOGGLE_LABEL

        self.btn_run = ctk.CTkButton(
            btn, text=f"运行 ({TOGGLE_LABEL})", command=on_run, height=36,
            fg_color=theme.ACCENT, hover_color="#255A3F", font=theme.FONT_UI,
        )
        self.btn_run.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        self.btn_stop = ctk.CTkButton(
            btn, text=f"停止 ({TOGGLE_LABEL})", command=on_stop, height=36,
            fg_color="#F3E8E6", hover_color="#E9D5D1", text_color=theme.ERR,
            font=theme.FONT_UI, state="disabled",
        )
        self.btn_stop.grid(row=0, column=1, sticky="ew", padx=8)

        self.btn_clear = ctk.CTkButton(
            btn, text="清日志", command=on_clear, height=36,
            fg_color="#EEF1EF", hover_color="#E2E7E4", text_color=theme.MUTED, font=theme.FONT_UI,
        )
        self.btn_clear.grid(row=0, column=2, sticky="ew", padx=8)

        self.btn_settings = ctk.CTkButton(
            btn, text="设置", command=on_settings or (lambda: None), height=36,
            fg_color="#EEF1EF", hover_color="#E2E7E4", text_color=theme.TEXT, font=theme.FONT_UI,
            state="normal" if on_settings else "disabled",
        )
        self.btn_settings.grid(row=0, column=3, sticky="ew", padx=(8, 0))

        # 仅 CTk 控件支持 configure(state=)；ttk.Treeview 通过 _locked 在事件里拦截。
        self._config_inputs: tuple[ctk.CTkBaseClass, ...] = (
            self.root_menu,
            self.loop_cb,
            self.params_box,
            self.btn_settings,
        )

    @property
    def locked(self) -> bool:
        return self._locked

    def set_locked(self, locked: bool) -> None:
        """运行中锁定配置区；树控件不碰 ttk state API。"""
        if self._locked == locked:
            return
        self._locked = locked
        cfg_state = "disabled" if locked else "normal"
        for widget in self._config_inputs:
            widget.configure(state=cfg_state)
        self.btn_run.configure(state="disabled" if locked else "normal")
        self.btn_stop.configure(state="normal" if locked else "disabled")

    def set_root_choices(self, choices: list[tuple[str, str]], *, selected_id: str | None = None) -> None:
        self._root_by_label = {label: rid for label, rid in choices}
        labels = [label for label, _ in choices] or ["(无 Flow)"]
        self.root_menu.configure(values=labels)
        pick = labels[0]
        if selected_id:
            for label, rid in choices:
                if rid == selected_id:
                    pick = label
                    break
        self.root_var.set(pick)
        self._rebuild_tree()

    def prepare_run(self) -> tuple[RunRequest | None, str]:
        """校验当前选择，组装后台运行请求。"""
        root_id = self.selected_root_id()
        entry_id = self.selected_entry_id()
        if not root_id or not entry_id:
            return None, "请选择 Flow"
        params, err = self._parse_params()
        if params is None:
            return None, err
        return (
            RunRequest(
                root_id=root_id,
                entry_id=entry_id,
                loop=self.loop_enabled(),
                params=params,
            ),
            "",
        )

    def _on_root_changed(self, _value: str) -> None:
        if self._locked:
            return
        self._rebuild_tree()
        self.params_hint.configure(text="")

    def _on_tree_select(self, _event: object | None = None) -> None:
        if self._locked:
            return
        entry_id = self.selected_entry_id()
        if entry_id:
            self._sync_params_for_entry(entry_id)
        self.params_hint.configure(text="")

    def _sync_params_for_entry(self, entry_id: str) -> None:
        if self._registry is None:
            return
        flow_id = self._registry.flow_of(entry_id)
        flow = self._registry.get(flow_id)
        if not isinstance(flow, Flow):
            return
        text = json.dumps(flow.params, ensure_ascii=False, indent=2) if flow.params else "{}"
        self.params_box.delete("1.0", "end")
        self.params_box.insert("1.0", text)

    def _rebuild_tree(self) -> None:
        for item in self._tree.get_children():
            self._tree.delete(item)
        self._tree_nodes.clear()
        self._registry = None
        root_id = self.selected_root_id()
        if not root_id:
            return
        root = get_root_flow(root_id)
        self._registry = FlowRegistry.build(root)
        tree = walk_tree(root)

        def _insert(parent: str, node: TreeNode) -> None:
            self._tree.insert(parent, "end", iid=node.id, text=node.name, open=True)
            self._tree_nodes[node.id] = node.name
            for child in node.children:
                _insert(node.id, child)

        self._tree.insert("", "end", iid=tree.id, text=tree.name, open=True)
        self._tree_nodes[tree.id] = tree.name
        for child in tree.children:
            _insert(tree.id, child)
        self._tree.selection_set(tree.id)
        self._tree.focus(tree.id)
        self._sync_params_for_entry(tree.id)

    def selected_root_id(self) -> str | None:
        return self._root_by_label.get(self.root_var.get().strip())

    def selected_entry_id(self) -> str | None:
        sel = self._tree.selection()
        if not sel:
            return self.selected_root_id()
        return str(sel[0])

    def selected_label(self) -> str:
        eid = self.selected_entry_id()
        if eid and eid in self._tree_nodes:
            return self._tree_nodes[eid]
        return self.root_var.get().strip()

    def loop_enabled(self) -> bool:
        return bool(self.loop_var.get())

    def _parse_params(self) -> tuple[dict | None, str]:
        raw = self.params_box.get("1.0", "end").strip() or "{}"
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            return None, f"JSON 格式错误: {exc.msg}"
        if not isinstance(data, dict):
            return None, "params 必须是 JSON 对象，例如 {}"
        return data, ""
