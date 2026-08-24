"""命令行入口。"""

from __future__ import annotations

import json

import typer
from rich.console import Console

from vision_bot import __version__
from vision_bot.logging_utils import setup_logging
from vision_bot.runtime.catalog import DEFAULT_ROOT_ID, get_root_flow
from vision_bot.runtime.config import RunConfig
from vision_bot.runtime.runner import run

app = typer.Typer(
    name="vision-bot",
    help="名将杀自动化",
    add_completion=False,
    no_args_is_help=True,
)
console = Console()


@app.command("run")
def run_cmd(
    flow_id: str = typer.Option(DEFAULT_ROOT_ID, "--flow", "-f", help="根 Flow id"),
    entry: str | None = typer.Option(None, "--entry", "-e", help="起始节点 id"),
    loop: bool = typer.Option(False, "--loop", "-l", help="循环执行"),
    params: str = typer.Option("{}", "--params", "-p", help="JSON 对象，覆盖 entry 所在 Flow 的 params"),
) -> None:
    """命令行直接运行。"""
    setup_logging()
    try:
        overrides = json.loads(params)
    except json.JSONDecodeError as exc:
        console.print(f"[red]JSON 格式错误: {exc.msg}[/red]")
        raise typer.Exit(code=2) from exc
    if not isinstance(overrides, dict):
        console.print("[red]params 必须是 JSON 对象[/red]")
        raise typer.Exit(code=2)
    root = get_root_flow(flow_id)
    config = RunConfig(entry_id=entry or root.id, loop=loop, params=overrides)
    report = run(root, config)
    console.print(f"完成 success={report.success} message={report.message}")
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


if __name__ == "__main__":
    app()
