"""Flow 树（供 UI 展示）。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from vision_bot.runtime.flow import Flow
from vision_bot.runtime.module import Module


@dataclass
class TreeNode:
    id: str
    name: str
    kind: Literal["flow", "module"]
    children: list[TreeNode]


def walk_tree(root: Flow) -> TreeNode:
    def _walk(node: Flow | Module) -> TreeNode:
        if isinstance(node, Module):
            return TreeNode(id=node.id, name=node.name, kind="module", children=[])
        return TreeNode(
            id=node.id,
            name=node.name,
            kind="flow",
            children=[_walk(child) for child in node.children],
        )

    return _walk(root)
