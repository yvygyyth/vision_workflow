"""根 Flow 目录与工具解析（应用注册表在 apps 层）。"""

from __future__ import annotations

from pathlib import Path

from vision_bot.apps.ming_jiang_sha.registry import (
    DEFAULT_ROOT_ID,
    ROOT_FLOWS as MJS_ROOT_FLOWS,
    tool_flows_for as mjs_tool_flows_for,
)
from vision_bot.apps.yi_huan.registry import (
    ROOT_FLOWS as YH_ROOT_FLOWS,
    tool_flows_for as yh_tool_flows_for,
)
from vision_bot.runtime.config import RunConfig
from vision_bot.runtime.flow import Flow
from vision_bot.runtime.runner import RunReport, run

ROOT_FLOWS = {**MJS_ROOT_FLOWS, **YH_ROOT_FLOWS}

__all__ = [
    "DEFAULT_ROOT_ID",
    "ROOT_FLOWS",
    "get_root_flow",
    "resolve_tool_flows",
    "root_flow_choices",
    "root_flow_ids",
    "run_root",
]


def root_flow_ids() -> list[str]:
    return list(ROOT_FLOWS)


def get_root_flow(root_id: str) -> Flow:
    builder = ROOT_FLOWS.get(root_id)
    if builder is None:
        raise KeyError(f"未知 Flow: {root_id}，可选: {list(ROOT_FLOWS)}")
    return builder()


def _tool_flows_for(root_id: str):
    if root_id in YH_ROOT_FLOWS:
        return yh_tool_flows_for(root_id)
    return mjs_tool_flows_for(root_id)


def resolve_tool_flows(root_id: str, tools: list[str] | None) -> list[Flow]:
    """解析要挂载的工具 Flow。``tools is None`` → 该 root 默认工具表全部。"""
    catalog = _tool_flows_for(root_id)
    if not catalog:
        return []
    ids = list(catalog) if tools is None else tools
    out: list[Flow] = []
    for tid in ids:
        builder = catalog.get(tid)
        if builder is None:
            raise KeyError(
                f"未知工具 Flow: {tid}（root={root_id}），可选: {list(catalog)}"
            )
        out.append(builder())
    return out


def run_root(
    root_id: str,
    config: RunConfig,
    *,
    cancel_event=None,
    base_dir: Path | None = None,
) -> RunReport:
    return run(
        get_root_flow(root_id),
        config,
        cancel_event=cancel_event,
        base_dir=base_dir,
        root_id=root_id,
    )


def root_flow_choices() -> list[tuple[str, str]]:
    """UI：(显示名, root_id)。"""
    return [(get_root_flow(rid).name, rid) for rid in ROOT_FLOWS]
