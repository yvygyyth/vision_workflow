"""PyInstaller 打包。"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist" / "VisionBot"
ENTRY = ROOT / "src" / "vision_bot" / "ui" / "__main__.py"


def main() -> int:
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        print("请先安装: pip install pyinstaller")
        return 1

    cmd = [
        sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--windowed", "--onedir",
        "--name", "VisionBot", "--paths", str(ROOT / "src"),
        "--collect-submodules", "vision_bot",
        "--collect-all", "customtkinter",
        str(ENTRY),
    ]
    subprocess.check_call(cmd, cwd=ROOT)

    data_src, data_dst = ROOT / "data", DIST / "data"
    if data_src.exists():
        if data_dst.exists():
            shutil.rmtree(data_dst)
        shutil.copytree(data_src, data_dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    print(f"\n完成: {DIST / 'VisionBot.exe'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
