"""日志桥：logging → 线程安全队列 → UI。"""

from __future__ import annotations

import logging
import queue
from collections.abc import Callable


class QueueLogHandler(logging.Handler):
    def __init__(self, log_queue: queue.Queue[str]) -> None:
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record: logging.LogRecord) -> None:
        try:
            self.log_queue.put(self.format(record))
        except Exception:  # noqa: BLE001
            self.handleError(record)


def attach_queue_handler(
    log_queue: queue.Queue[str],
    *,
    level: int = logging.INFO,
) -> QueueLogHandler:
    handler = QueueLogHandler(log_queue)
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s", "%H:%M:%S"))
    root = logging.getLogger()
    root.addHandler(handler)
    return handler


def drain_queue(log_queue: queue.Queue[str], append: Callable[[str], None], *, limit: int = 200) -> None:
    for _ in range(limit):
        try:
            line = log_queue.get_nowait()
        except queue.Empty:
            break
        append(line)
