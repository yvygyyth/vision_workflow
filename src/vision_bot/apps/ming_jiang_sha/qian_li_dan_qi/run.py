"""千里单骑入口。"""

from __future__ import annotations

import logging
import threading
from pathlib import Path

from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.build import build_qian_li_dan_qi
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.signals import build_registry
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.state import bind_battle_state, clear_battle_state
from vision_bot.core.paths import project_root
from vision_bot.runtime import RunContext, run_root
from vision_bot.runtime.runner import RunReport

logger = logging.getLogger(__name__)


def run(
    *,
    base_dir: Path | None = None,
    cancel_event: threading.Event | None = None,
    wu_jiang: str = "吕布",
) -> RunReport:
    root = (base_dir or project_root()).resolve()
    ctx = RunContext(
        base_dir=root,
        registry=build_registry(),
        cancel_event=cancel_event,
        params={"wu_jiang": wu_jiang},
    )
    bind_battle_state(ctx)
    logger.info("千里单骑启动 base_dir=%s", root)
    try:
        flow = build_qian_li_dan_qi()
        return run_root(flow, ctx)
    finally:
        clear_battle_state(ctx)
