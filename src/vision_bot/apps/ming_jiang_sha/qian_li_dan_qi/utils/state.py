"""千里单骑局内状态（兼容导出）。"""

from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.state import (
    VARS_BATTLE_STATE,
    BattleState,
    bind_battle_state,
    clear_battle_state,
    get_battle_state,
)

VARS_KEY = VARS_BATTLE_STATE

__all__ = [
    "VARS_KEY",
    "VARS_BATTLE_STATE",
    "BattleState",
    "bind_battle_state",
    "clear_battle_state",
    "get_battle_state",
]
