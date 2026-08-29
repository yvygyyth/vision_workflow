"""识图公共 API。

使用前需先 :func:`bind` 绑定 ``base_dir`` 等默认值（:func:`~vision_bot.runtime.runner.run` 会自动完成）。
业务与动作链均通过 :func:`find` / :func:`find_once` 识图；底层 OpenCV 实现在 ``core.vision``，不对外暴露。

返回值统一为 :class:`~vision_bot.runtime.result.Result`：

- ``ok=True`` 时，``value`` 为 :class:`~vision_bot.core.models.MatchResult`
  或 ``list[MatchResult]``（``find_all``）
- ``ok=False`` 时，``message`` 为失败原因，``value`` 可能携带末次匹配详情

:func:`find` 默认按会话 ``timeout`` 轮询等待出现；:func:`find_once` 只查一轮
（``timeout=0``），适合确认某图已消失。
"""

from vision_bot.vision.find import find, find_all, find_once, resolve_path
from vision_bot.vision.session import bind

__all__ = ["bind", "find", "find_all", "find_once", "resolve_path"]
