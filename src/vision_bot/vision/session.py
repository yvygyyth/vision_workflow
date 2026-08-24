"""识图模块默认配置。

任务启动时通过 :func:`vision.bind` 注入一次；之后 ``find`` / ``wait_any`` 等
会自动读取这里的 ``base_dir``、``options``、``cancelled``。
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from vision_bot.core.models import MatchOptions


@dataclass
class VisionSession:
    """识图模块当前生效的全局默认值。"""

    base_dir: Path | None = None
    """项目根目录；相对路径模板会拼在此目录下解析为绝对路径。"""

    options: MatchOptions = field(default_factory=MatchOptions)
    """未在单次调用中显式传入的参数，从此处继承（阈值、轮询间隔等）。"""

    cancelled: Callable[[], bool] | None = None
    """取消检查函数；返回 ``True`` 时识图轮询立即中断。"""


_session = VisionSession()


def bind(
    *,
    base_dir: Path | None = None,
    options: MatchOptions | None = None,
    cancelled: Callable[[], bool] | None = None,
) -> None:
    """绑定识图模块默认值（任务启动时调用一次即可）。

    Parameters
    ----------
    base_dir:
        项目根目录。传入后，``find("data/.../a.png")`` 会解析为
        ``base_dir / "data/.../a.png"``。未绑定且传入相对路径时，
        按当前工作目录解析。
    options:
        任务级默认匹配参数（``threshold``、``interval``、``region`` 等）。
        单次调用传入的参数会覆盖对应字段。
    cancelled:
        取消回调，签名 ``() -> bool``。用户停止任务时应返回 ``True``，
        识图等待循环会抛出 :class:`~vision_bot.runtime.cancel.CancelledError`
        或返回失败。
    """
    if base_dir is not None:
        _session.base_dir = base_dir
    if options is not None:
        _session.options = options
    if cancelled is not None:
        _session.cancelled = cancelled


def session() -> VisionSession:
    """返回当前识图模块默认配置（一般无需直接访问）。"""
    return _session
