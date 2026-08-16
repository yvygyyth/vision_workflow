"""用 PyInstaller 打成 Windows 桌面程序（onedir；流程打进二进制，data 放 exe 旁）。"""

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
        # 内置流程随程序打包；新增子流程不必再改这里
        "--collect-submodules",
        "vision_workflow.apps",
        "--collect-all",
        "customtkinter",
        str(ENTRY),
    ]
    print(" ".join(cmd))
    subprocess.check_call(cmd, cwd=ROOT)

    data_src = ROOT / "data"
    data_dst = DIST / "data"
    if data_src.exists():
        if data_dst.exists():
            shutil.rmtree(data_dst)
        shutil.copytree(data_src, data_dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        print(f"copied {data_src} -> {data_dst}")

    print(f"\n完成: {DIST / 'VisionWorkflow.exe'}")
    print("可将整个 dist/VisionWorkflow 文件夹分发；流程已打进程序，模板图在 exe 同级 data/。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
