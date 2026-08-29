"""识图公共 API。

使用前需先 :func:`bind` 绑定 ``base_dir`` 等默认值（:func:`~vision_bot.runtime.runner.run` 会自动完成）。

- :func:`find`：默认慢查（会话 timeout）
- :func:`snap`：快查（``timeout=0``）
- 二者均支持单图 / 多图；底层为 ``find_image`` / ``find_images``
"""

from vision_bot.vision.find import (
    ScreenSnapshot,
    find,
    find_all,
    resolve_path,
    snap,
)
from vision_bot.vision.session import bind

__all__ = [
    "bind",
    "find",
    "find_all",
    "resolve_path",
    "snap",
    "ScreenSnapshot",
]
