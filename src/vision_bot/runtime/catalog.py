"""根 Flow 目录（替代 Job 注册表）。"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from vision_bot.apps.ming_jiang_sha.ba_wang_zhi_luan.build import build as build_ba_wang
from vision_bot.apps.ming_jiang_sha.fee_day.build import build_fee_day
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.build import build_qian_li_dan_qi
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.signals import build_registry as build_qldq_registry
from vision_bot.perception.signal import SignalRegistry
from vision_bot.runtime.config import RunConfig
from vision_bot.runtime.flow import Flow
from vision_bot.runtime.runner import RunReport, run

RootBuilder = Callable[[], Flow]
RegistryBuilder = Callable[[], SignalRegistry]

ROOT_FLOWS: dict[str, RootBuilder] = {
    "qldq": build_qian_li_dan_qi,
    "ba_wang": build_ba_wang,
    "fee_day": build_fee_day,
}

ROOT_REGISTRIES: dict[str, RegistryBuilder] = {
    "qldq": build_qldq_registry,
}

DEFAULT_ROOT_ID = "qldq"


def root_flow_ids() -> list[str]:
    return list(ROOT_FLOWS.keys())


def get_root_flow(root_id: str) -> Flow:
    builder = ROOT_FLOWS.get(root_id)
    if builder is None:
        raise KeyError(f"未知 Flow: {root_id}，可选: {list(ROOT_FLOWS)}")
    return builder()


def registry_for(root_id: str) -> SignalRegistry:
    builder = ROOT_REGISTRIES.get(root_id)
    if builder is None:
        return SignalRegistry()
    return builder()


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
        registry=registry_for(root_id),
        cancel_event=cancel_event,
        base_dir=base_dir,
    )


def root_flow_choices() -> list[tuple[str, str]]:
    """UI：(显示名, root_id)。"""
    return [(get_root_flow(rid).name, rid) for rid in ROOT_FLOWS]
