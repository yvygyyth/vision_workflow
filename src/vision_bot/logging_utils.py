"""日志工具。"""

from __future__ import annotations

import logging

from vision_bot.core.paths import project_root


def setup_logging(*, gui: bool = False, level: int = logging.INFO) -> logging.Logger:
    log_dir = project_root() / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "vision_bot.log"

    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(level)

    if not gui:
        from rich.logging import RichHandler

        console = RichHandler(rich_tracebacks=True, markup=True, show_path=False)
        console.setLevel(level)
        console.setFormatter(logging.Formatter("%(message)s"))
        root.addHandler(console)

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(level)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    )
    root.addHandler(file_handler)
    return logging.getLogger("vision_bot")
