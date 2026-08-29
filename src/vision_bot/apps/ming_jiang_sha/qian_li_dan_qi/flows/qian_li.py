"""千里单骑根 Flow：全局画面重定位。"""

from __future__ import annotations

import logging

from vision_bot.apps.ming_jiang_sha.paths import QLDQ
from vision_bot.runtime.context import RunContext
from vision_bot.runtime.relocate import RelocateRule
from vision_bot.vision import snap

logger = logging.getLogger(__name__)

_UN_START = f"{QLDQ}/enter_battle/un_start.png"
_START = f"{QLDQ}/enter_battle/start.png"
_BATTLE_INTERFACE = f"{QLDQ}/enter_battle/battle_interface.png"


def _when_pick(ctx: RunContext) -> bool:
    shot = snap(_UN_START, _START)
    logger.info(
        "qldq relocate pick un_start=%s start=%s",
        shot.found(_UN_START),
        shot.found(_START),
    )
    return shot.race


def _when_battle_interface(ctx: RunContext) -> bool:
    ok = snap(_BATTLE_INTERFACE).ok
    logger.info("qldq relocate battle_interface=%s", ok)
    return ok


relocate: list[RelocateRule] = [
    RelocateRule(when=_when_pick, then=None),
    RelocateRule(when=_when_battle_interface, then="qldq.battle_hub"),
]
