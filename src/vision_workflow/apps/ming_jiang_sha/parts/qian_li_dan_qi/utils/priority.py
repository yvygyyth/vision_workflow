"""武将赠礼优先配置（越靠前越优先；按需改表即可）。"""

from __future__ import annotations

from vision_workflow.apps.ming_jiang_sha.parts.qian_li_dan_qi.utils.rewards import (
    GeneralPriority,
    RewardKind,
)

PRIORITY: list[GeneralPriority] = [
    GeneralPriority("马超", (RewardKind.TOKEN, RewardKind.HELP)),
    GeneralPriority("吕布", (RewardKind.HELP, RewardKind.TOKEN)),
    GeneralPriority("陆逊", (RewardKind.CARD,)),
]
