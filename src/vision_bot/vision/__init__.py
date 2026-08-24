"""识图公共 API。

使用前需先 :func:`bind` 绑定 ``base_dir`` 等默认值（:func:`~vision_bot.runtime.runner.run` 会自动完成）。
业务代码通常只需传入模板图路径；其余参数按需特调。

返回值统一为 :class:`~vision_bot.runtime.result.Result`：

- ``ok=True`` 时，``value`` 为 :class:`~vision_bot.core.models.MatchResult`
  或 ``list[MatchResult]``（``find_all``）
- ``ok=False`` 时，``message`` 为失败原因，``value`` 可能携带末次匹配详情
"""

from vision_bot.vision.find import find, find_all, resolve_path, wait_any
from vision_bot.vision.session import bind

__all__ = ["bind", "find", "find_all", "resolve_path", "wait_any"]
