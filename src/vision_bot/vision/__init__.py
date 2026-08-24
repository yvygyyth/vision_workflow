"""识图（独立于运行时上下文）。"""

from vision_bot.vision.find import find, find_all, resolve_path, wait_any
from vision_bot.vision.session import bind

__all__ = ["bind", "find", "find_all", "resolve_path", "wait_any"]
