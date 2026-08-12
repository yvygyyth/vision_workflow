"""用 PyInstaller 打成 Windows 桌面程序（onedir，config/data 放在 exe 旁）。"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist" / "VisionWorkflow"
ENTRY = ROOT / "src" / "vision_workflow" / "ui" / "__main__.py"


def main() -> int:
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        print("请先安装: pip install pyinstaller")
        return 1

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--windowed",
        "--onedir",
        "--name",
        "VisionWorkflow",
        "--paths",
        str(ROOT / "src"),
        "--paths",
        str(ROOT),
        "--hidden-import",
        "config.flow",
        "--hidden-import",
        "config.actions",
        "--collect-all",
        "customtkinter",
        str(ENTRY),
    ]
    print(" ".join(cmd))
    subprocess.check_call(cmd, cwd=ROOT)

    for name in ("config", "data"):
        src = ROOT / name
        dst = DIST / name
        if not src.exists():
            continue
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        print(f"copied {src} -> {dst}")

    print(f"\n完成: {DIST / 'VisionWorkflow.exe'}")
    print("可将整个 dist/VisionWorkflow 文件夹分发；config 与 data 在 exe 同级，可直接改。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
