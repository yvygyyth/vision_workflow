"""命令行入口。"""

from __future__ import annotations

import typer
from rich.console import Console

from vision_bot import __version__
from vision_bot.logging_utils import setup_logging
from vision_bot.start import DEFAULT_JOB_ID, start

app = typer.Typer(
    name="vision-bot",
    help="千里单骑自动化",
    add_completion=False,
    no_args_is_help=True,
)
console = Console()


@app.command("run")
def run_cmd(
    job_id: str = typer.Option(DEFAULT_JOB_ID, "--job", "-j", help="任务 id"),
    wu_jiang: str = typer.Option("吕布", "--wu-jiang", help="武将名（千里单骑）"),
) -> None:
    """命令行直接运行。"""
    setup_logging()
    report = start(job_id, wu_jiang=wu_jiang)
    console.print(f"完成 success={report.success} outcome={report.outcome}")
    if report.path:
        console.print("路径: " + " → ".join(report.path))
    raise typer.Exit(code=0 if report.success else 1)


@app.command("ui")
def ui_cmd() -> None:
    """打开桌面界面。"""
    from vision_bot.ui import run_app

    run_app()


@app.command("version")
def version_cmd() -> None:
    console.print(__version__)
