"""UI 信号定义：模板路径 + 匹配参数（状态机与 Flow 共用）。"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from vision_bot.core.models import MatchOptions

Region = tuple[int, int, int, int]


@dataclass(frozen=True)
class Signal:
    """单个 UI 特征。"""

    template: str
    """相对 base_dir 或绝对路径。"""
    threshold: float = 0.8
    region: Region | None = None
    region_fit: bool = True
    grayscale: bool = True

    def match_options(self) -> MatchOptions:
        return MatchOptions(
            threshold=self.threshold,
            timeout=0.0,
            region=self.region,
            region_fit=self.region_fit,
            grayscale=self.grayscale,
        )


@dataclass
class SignalRegistry:
    """signal_id → Signal；业务在 apps 下集中注册。"""

    _signals: dict[str, Signal] = field(default_factory=dict)

    def register(self, signal_id: str, signal: Signal) -> None:
        if signal_id in self._signals:
            raise ValueError(f"重复 signal_id: {signal_id}")
        self._signals[signal_id] = signal

    def get(self, signal_id: str) -> Signal:
        if signal_id not in self._signals:
            raise KeyError(f"未知 signal: {signal_id}")
        return self._signals[signal_id]

    def ids(self) -> list[str]:
        return list(self._signals.keys())

    def subset(self, keys: set[str]) -> dict[str, Signal]:
        return {k: self.get(k) for k in keys}

    def resolve_path(self, signal_id: str, base_dir: Path) -> Path:
        sig = self.get(signal_id)
        path = Path(sig.template)
        if path.is_absolute():
            return path
        return (base_dir / path).resolve()
