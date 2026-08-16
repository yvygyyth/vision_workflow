"""好友送花流程动作。"""

from __future__ import annotations

import logging
import time

from vision_workflow.apps.ming_jiang_sha.common.paths import DATA_ROOT
from vision_workflow.events import click, do, input_text, move
from vision_workflow.module import EventFn, ModuleContext
from vision_workflow.status import REJECTED, OutcomeKey

logger = logging.getLogger(__name__)

_DIR = f"{DATA_ROOT}/song_hua"

click_entry: EventFn = do(
    move().image(f"{_DIR}/hao_you.png"),
    click(),
)

focus_search_input: EventFn = do(
    move().image(f"{_DIR}/sou_suo.png"),
    click().pause(0.3),
)


def type_Friend(m: ModuleContext) -> OutcomeKey:
    """写入好友名（入参 friend_name）。"""
    name = str(m.params.get("friend_name", "张飞")).strip()
    if not name:
        m.reason = "入参 friend_name 为空"
        return REJECTED
    logger.info("type_Friend %s", name)
    time.sleep(0.2)
    return input_text(name).paste().pause(0.2).execute()(m)
