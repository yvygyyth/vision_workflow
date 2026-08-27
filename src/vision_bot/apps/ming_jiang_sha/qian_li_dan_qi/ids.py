"""千里单骑 · 节点 id 拼接。"""

from __future__ import annotations


def qmod(flow_path: str, step: str) -> str:
    return f"qldq.{flow_path}.{step}"
