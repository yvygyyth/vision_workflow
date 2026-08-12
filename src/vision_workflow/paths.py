"""项目根路径：开发态与 PyInstaller 打包态统一。"""

from __future__ import annotations

import sys
from pathlib import Path


def project_root() -> Path:
    """可写资源根（exe 旁或仓库根）：模板图 data/、日志等。"""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    # src/vision_workflow/paths.py → 仓库根
    return Path(__file__).resolve().parents[2]
