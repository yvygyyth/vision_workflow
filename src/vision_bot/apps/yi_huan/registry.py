"""异环：根 Flow 注册。"""

from __future__ import annotations

from collections.abc import Callable

from vision_bot.apps.yi_huan.dian_zhang_te_gong.build import build_dian_zhang_te_gong
from vision_bot.runtime.flow import Flow

FlowBuilder = Callable[[], Flow]

ROOT_FLOWS: dict[str, FlowBuilder] = {
    "dian_zhang_te_gong": build_dian_zhang_te_gong,
}


def tool_flows_for(root_id: str) -> dict[str, FlowBuilder]:
    return {}
