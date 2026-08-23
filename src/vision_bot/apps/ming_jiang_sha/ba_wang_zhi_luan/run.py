"""八王之乱入口。"""

from __future__ import annotations

import logging
import threading
from pathlib import Path

from vision_bot.apps.ming_jiang_sha.ba_wang_zhi_luan.build import build
from vision_bot.core.paths import project_root
from vision_bot.perception.signal import SignalRegistry
from vision_bot.runtime import RunContext, run_root
from vision_bot.runtime.runner import RunReport

logger = logging.getLogger(__name__)


def run(
    *,
    base_dir: Path | None = None,
    cancel_event: threading.Event | None = None,
) -> RunReport:
    root = (base_dir or project_root()).resolve()
    ctx = RunContext(
        base_dir=root,
        registry=SignalRegistry(),
        cancel_event=cancel_event,
    )
    logger.info("八王之乱启动 base_dir=%s", root)
    return run_root(build(), ctx)
