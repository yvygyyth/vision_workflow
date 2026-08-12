"""命令行入口。"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from vision_workflow import __version__
from vision_workflow.config import reload_settings
from vision_workflow.flow import FlowRunner, load_flow_module
from vision_workflow.logging_utils import setup_logging

app = typer.Typer(
    name="vision-workflow",
    help="模块组成流程、流程组成工作流",
    add_completion=False,
    no_args_is_help=True,
)
console = Console()


@app.command("flow")
def flow_cmd(
    target: str = typer.Argument(
        ...,
        help="Python 流程模块，如 config.flow 或 config/flow.py",
    ),
    start: Optional[str] = typer.Option(
        None,
        "--start",
        "-s",
        help="从流程 id 或 flow.module 开始",
    ),
    only: Optional[str] = typer.Option(
        None,
        "--only",
        help="只执行某一个模块（module 或 flow.module）",
    ),
    dry_run: bool = typer.Option(False, "--dry-run", help="不真实操作鼠标"),
    base_dir: Optional[Path] = typer.Option(None, "--base-dir", help="模板图相对路径基准目录"),
    json_out: bool = typer.Option(False, "--json", help="JSON 输出"),
) -> None:
    """执行 Workflow（模块组成流程，流程再组合）。"""
    cwd = str(Path.cwd())
    if cwd not in sys.path:
        sys.path.insert(0, cwd)

    setup_logging(reload_settings())
    workflow = load_flow_module(target)
    runner = FlowRunner(
        workflow,
        base_dir=base_dir,
        dry_run=True if dry_run else None,
    )
    if only:
        settled = runner.run_module(only)
        if json_out:
            console.print_json(
                {
                    "ok": settled.ok,
                    "error": settled.error,
                    "feedback": settled.feedback,
                }
            )
        else:
            console.print(f"module={only} ok={settled.ok} | {settled.feedback or settled.error}")
        raise typer.Exit(code=0 if settled.ok else 1)

    result = runner.run(start=start)
    if json_out:
        console.print_json(result.model_dump_json())
    else:
        table = Table(title=f"Workflow · {result.flow_name}")
        table.add_column("字段")
        table.add_column("值")
        table.add_row("success", str(result.success))
        table.add_row("feedback", result.feedback or result.message)
        table.add_row("message", result.message)
        table.add_row("path", " → ".join(result.path) or "(empty)")
        for step in result.steps:
            table.add_row(
                f"step:{step.step_id}",
                step.feedback or f"ok={step.success} | {step.message}",
            )
        console.print(table)
    raise typer.Exit(code=0 if result.success else 1)


@app.command("info")
def info_cmd() -> None:
    """查看当前运行配置。"""
    cfg = reload_settings()
    console.print(f"[bold]vision-workflow[/bold] v{__version__}")
    console.print(f"env       : {cfg.app.get('env')}")
    console.print(f"log_level : {cfg.logging.level}")
    console.print(f"root_dir  : {cfg.root_dir}")


@app.command("version")
def version_cmd() -> None:
    console.print(__version__)


if __name__ == "__main__":
    app()
