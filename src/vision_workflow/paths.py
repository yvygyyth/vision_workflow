"""项目根路径：开发态与 PyInstaller 打包态统一。"""

from __future__ import annotations

import sys
from pathlib import Path


def project_root() -> Path:
    """可写/可配置的项目根（exe 旁或仓库根）。"""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    # src/vision_workflow/paths.py → 仓库根
    return Path(__file__).resolve().parents[2]


def ensure_runtime_path() -> Path:
    """保证项目根在 sys.path，便于 import config.*。"""
    root = project_root()
    root_s = str(root)
    if root_s not in sys.path:
        sys.path.insert(0, root_s)
    return root
