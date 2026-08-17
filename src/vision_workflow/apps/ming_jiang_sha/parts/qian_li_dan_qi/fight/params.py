"""开打 Flow 入参。"""

from __future__ import annotations

from enum import StrEnum

PARAM_GIFT = "gift"


class FightGift(StrEnum):
    """本场战斗结算后是否选赠礼。"""

    WITH = "with"
    WITHOUT = "without"
