"""识图匹配相关用户设置（可持久化）。"""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields


@dataclass
class MatchSettings:
    """识图 4 项配置。"""

    baseline_width: int = 2560
    baseline_height: int = 1440
    """模板采集基准分辨率。"""
    scale_min: float = 0.90
    """多尺度下限（相对基准换算 scale）。"""
    scale_max: float = 1.10
    """多尺度上限。"""
    multi_scale: bool = True
    """是否开启多尺度匹配；关闭则只用基准换算的单一 scale。"""

    def baseline_label(self) -> str:
        return f"{self.baseline_width}x{self.baseline_height}"

    def validate(self) -> MatchSettings:
        w = max(1, int(self.baseline_width))
        h = max(1, int(self.baseline_height))
        lo = float(self.scale_min)
        hi = float(self.scale_max)
        if lo <= 0 or hi <= 0:
            raise ValueError("scale_min / scale_max 必须 > 0")
        if lo > hi:
            lo, hi = hi, lo
        return MatchSettings(
            baseline_width=w,
            baseline_height=h,
            scale_min=lo,
            scale_max=hi,
            multi_scale=bool(self.multi_scale),
        )

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict | None) -> MatchSettings:
        if not data:
            return cls()
        allowed = {f.name for f in fields(cls)}
        raw = {k: v for k, v in data.items() if k in allowed}
        return cls(**raw).validate()
