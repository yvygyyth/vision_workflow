"""武将赠礼优先配置（越靠前越优先；按需改表即可）。"""

from __future__ import annotations

from vision_workflow.apps.ming_jiang_sha.parts.qian_li_dan_qi.utils.rewards import (
    GeneralPriority,
    RewardKind,
)

PRIORITY: list[GeneralPriority] = [
    GeneralPriority("王异", (RewardKind.TOKEN,)),
    GeneralPriority("荀彧", (RewardKind.TOKEN,)),
    GeneralPriority("甘宁", (RewardKind.TOKEN, RewardKind.BUFF)),
    GeneralPriority("刘表", (RewardKind.TOKEN, RewardKind.BUFF)),
    GeneralPriority("萧何", (RewardKind.TOKEN,)),
    GeneralPriority("曹操", (RewardKind.TOKEN,)),
    GeneralPriority("韩信", (RewardKind.TOKEN,)),
    GeneralPriority("吕布", (RewardKind.TOKEN,)),
    GeneralPriority("马超", (RewardKind.BUFF,)),
    GeneralPriority("吕雉", (RewardKind.TOKEN,)),
    GeneralPriority("关羽", (RewardKind.TOKEN,)),
    GeneralPriority("左慈", (RewardKind.TOKEN,)),
    GeneralPriority("周勃", (RewardKind.TOKEN,)),
    GeneralPriority("鲁肃", (RewardKind.HELP, RewardKind.BUFF)),
    GeneralPriority("庞统", (RewardKind.TOKEN,)),
    GeneralPriority("华佗", (RewardKind.TOKEN,)),
]

# 优先表里没有的武将：默认关键奖励序（也用作全局类别回退）
DEFAULT_KEY_REWARDS: tuple[RewardKind, ...] = (
    RewardKind.BUFF,
    RewardKind.HELP,
    RewardKind.CARD,
    RewardKind.JOINT,
    RewardKind.TOKEN,
)

# 主路径都不满足时按类别回退（与表外武将默认一致）
FALLBACK_KIND_ORDER: tuple[RewardKind, ...] = DEFAULT_KEY_REWARDS

# 巴清商店关键信物（越靠前越优先；店里有才会出现，不必再查背包）
TOKEN_PRIORITY: list[str] = [
    "麻衣",
    "熏炉",
    "行囊",
    "铃铛",
    "典籍",
    "《孟德新书》",
    "象棋",
    "《九章律》",
    "鸠杯",
    "飞将翎",
    "纱锦囊",
    "皇后之玺",
    "薄曲",
    "青囊书",
    "美人草",
    "凤毛",
    #出牌阶段开始时，你每有1点体力上限，就出杀次数+1。
    "将印"
]
