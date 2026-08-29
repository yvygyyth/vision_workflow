"""名将杀：根 Flow 与共用工具 Flow 注册。"""

from __future__ import annotations

from collections.abc import Callable

from vision_bot.apps.ming_jiang_sha.ba_wang_zhi_luan.build import build as build_ba_wang
from vision_bot.apps.ming_jiang_sha.fee_day.build import build_fee_day
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.build import build_qian_li_dan_qi
from vision_bot.apps.ming_jiang_sha.tools.battle import build_battle
from vision_bot.runtime.flow import Flow

FlowBuilder = Callable[[], Flow]

# 业务根（UI 可选）
ROOT_FLOWS: dict[str, FlowBuilder] = {
    "qldq": build_qian_li_dan_qi,
    "ba_wang": build_ba_wang,
    "fee_day": build_fee_day,
}

# 共用工具（RunConfig.tools=None 时默认挂载，不进业务树）
TOOL_FLOWS: dict[str, FlowBuilder] = {
    "mjs.battle": build_battle,
}

DEFAULT_ROOT_ID = "qldq"


def tool_flows_for(root_id: str) -> dict[str, FlowBuilder]:
    """某 root 启动时应挂载的工具表（目前全模式共用）。"""
    return dict(TOOL_FLOWS)
