"""识图匹配相关用户设置（可持久化）。"""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields


@dataclass
class MatchSettings:
    """识图配置（基准只读；多尺度参数可改）。"""

    baseline_width: int = 2560
    baseline_height: int = 1440
    """模板采集基准分辨率（只读，以代码默认为准）。"""
    scale_min: float = 0.90
    """多尺度下限（相对基准换算 scale）。"""
    scale_max: float = 1.10
    """多尺度上限。"""
    scale_samples: int = 5
    """多尺度采样档数（含两端，至少 2）。"""
    multi_scale: bool = True
    """是否开启多尺度匹配；关闭则只用基准换算的单一 scale。"""

    def baseline_label(self) -> str:
        return f"{self.baseline_width}x{self.baseline_height}"

    def validate(self) -> MatchSettings:
        w = max(1, int(self.baseline_width))
        h = max(1, int(self.baseline_height))
        lo = float(self.scale_min)
        hi = float(self.scale_max)
        samples = int(self.scale_samples)
        if lo <= 0 or hi <= 0:
            raise ValueError("scale_min / scale_max 必须 > 0")
        if lo > hi:
            lo, hi = hi, lo
        if samples < 2:
            raise ValueError("scale_samples（分几档）至少为 2")
        return MatchSettings(
            baseline_width=w,
            baseline_height=h,
            scale_min=lo,
            scale_max=hi,
            scale_samples=samples,
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
        # 基准分辨率以代码默认为准，忽略文件中的改写
        defaults = cls()
        raw["baseline_width"] = defaults.baseline_width
        raw["baseline_height"] = defaults.baseline_height
        return cls(**raw).validate()
