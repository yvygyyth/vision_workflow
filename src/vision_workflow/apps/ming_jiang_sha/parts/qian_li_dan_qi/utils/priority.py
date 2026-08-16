"""武将赠礼优先配置（越靠前越优先；按需改表即可）。"""

from __future__ import annotations

from vision_workflow.apps.ming_jiang_sha.parts.qian_li_dan_qi.utils.rewards import (
    GeneralPriority,
    RewardKind,
)

PRIORITY: list[GeneralPriority] = [
    GeneralPriority("马超", (RewardKind.TOKEN, RewardKind.BUFF)),
    GeneralPriority("吕布", (RewardKind.BUFF, RewardKind.TOKEN)),
    GeneralPriority("陆逊", (RewardKind.CARD,)),
]

# 巴清商店关键信物（越靠前越优先；店里有才会出现，不必再查背包）
TOKEN_PRIORITY: list[str] = [
    "草鞋",
    "念珠",
]
