"""日志工具。"""

from __future__ import annotations

import logging
from pathlib import Path

from rich.logging import RichHandler

from vision_workflow.config import RuntimeConfig


def setup_logging(cfg: RuntimeConfig) -> logging.Logger:
    log_dir = cfg.resolve_path(cfg.logging.dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "vision_workflow.log"

    level = getattr(logging, cfg.logging.level.upper(), logging.INFO)
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(level)

    console = RichHandler(rich_tracebacks=True, markup=True, show_path=False)
    console.setLevel(level)
    console.setFormatter(logging.Formatter("%(message)s"))

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(level)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    )

    root.addHandler(console)
    root.addHandler(file_handler)
    return logging.getLogger("vision_workflow")
