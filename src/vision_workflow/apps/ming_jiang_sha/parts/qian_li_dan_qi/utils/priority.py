"""武将赠礼优先配置（越靠前越优先；按需改表即可）。"""

from __future__ import annotations

from vision_workflow.apps.ming_jiang_sha.parts.qian_li_dan_qi.utils.rewards import (
    GeneralPriority,
    RewardKind,
)

PRIORITY: list[GeneralPriority] = [
    GeneralPriority("马超", (RewardKind.BUFF,)),
    GeneralPriority("吕布", (RewardKind.TOKEN)),
    GeneralPriority("鲁肃", (RewardKind.HELP, RewardKind.BUFF)),
]

# 巴清商店关键信物（越靠前越优先；店里有才会出现，不必再查背包）
TOKEN_PRIORITY: list[str] = [
    "麻衣",
    "熏炉",
    "行囊",
    "铃铛",
    "典籍",
    "《孟德新书》",
    "象棋",
    "鸠杯",
    "飞将翎",
    "纱锦囊"
    "薄曲",
    "青囊书",
    "凤毛",
]
