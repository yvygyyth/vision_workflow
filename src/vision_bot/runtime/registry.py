"""Flow 树索引（构建期注册）。"""

from __future__ import annotations

from dataclasses import dataclass, field

from vision_bot.runtime.flow import Flow
from vision_bot.runtime.jump import JumpTargetError
from vision_bot.runtime.module import Module


@dataclass
class FlowRegistry:
    nodes: dict[str, Flow | Module] = field(default_factory=dict)
    parent_flow: dict[str, str] = field(default_factory=dict)
    child_index: dict[str, int] = field(default_factory=dict)

    @classmethod
    def build(cls, root: Flow) -> FlowRegistry:
        reg = cls()
        reg._walk(root, parent_id=None)
        return reg

    def _walk(self, flow: Flow, *, parent_id: str | None) -> None:
        if flow.id in self.nodes:
            raise ValueError(f"节点 id 重复: {flow.id}")
        self.nodes[flow.id] = flow
        if parent_id is not None:
            self.parent_flow[flow.id] = parent_id

        for i, child in enumerate(flow.children):
            if isinstance(child, Module):
                if child.id in self.nodes:
                    raise ValueError(f"节点 id 重复: {child.id}")
                self.nodes[child.id] = child
                self.parent_flow[child.id] = flow.id
                self.child_index[child.id] = i
            else:
                self._walk(child, parent_id=flow.id)

    def get(self, node_id: str) -> Flow | Module:
        if node_id not in self.nodes:
            raise JumpTargetError(f"节点不存在: {node_id}")
        return self.nodes[node_id]

    def next_sibling_index(self, node_id: str) -> tuple[str, int] | None:
        """返回 (父 Flow id, 下一兄弟 index)；无兄弟则 None。"""
        parent_id = self.parent_flow.get(node_id)
        if parent_id is None:
            return None
        parent = self.nodes[parent_id]
        assert isinstance(parent, Flow)
        idx = self.child_index[node_id]
        nxt = idx + 1
        if nxt >= len(parent.children):
            return None
        return parent_id, nxt
