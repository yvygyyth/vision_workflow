"""命令行入口。"""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from vision_workflow import __version__
from vision_workflow.config import reload_settings
from vision_workflow.flow import WorkflowRunner
from vision_workflow.flows import WORKFLOW, get_workflow
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
    workflow_id: str | None = typer.Option(
        None,
        "--workflow",
        "-w",
        help="复杂流程 id；默认入口复杂流程",
    ),
    start: str | None = typer.Option(
        None,
        "--start",
        "-s",
        help="调试：从子流程 id 或 flow.module 开始",
    ),
    only: str | None = typer.Option(
        None,
        "--only",
        help="调试：只执行某一个模块（module 或 flow.module）",
    ),
    base_dir: Path | None = typer.Option(None, "--base-dir", help="模板图相对路径基准目录"),
    json_out: bool = typer.Option(False, "--json", help="JSON 输出"),
) -> None:
    """执行内置复杂流程。"""
    setup_logging(reload_settings())
    workflow = get_workflow(workflow_id) if workflow_id else WORKFLOW
    runner = WorkflowRunner(workflow, base_dir=base_dir)
    if only:
        settled = runner.run_module(only)
        if json_out:
            console.print_json(
                {
                    "status": settled.status.value,
                    "ok": settled.ok,
                    "error": settled.error,
                    "feedback": settled.feedback,
                }
            )
        else:
            console.print(
                f"module={only} status={settled.status.value} | {settled.feedback or settled.error}"
            )
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


@app.command("ui")
def ui_cmd() -> None:
    """打开桌面界面。"""
    from vision_workflow.ui import run_app

    run_app()


@app.command("info")
def info_cmd() -> None:
    """查看当前运行配置与显示参数。"""
    from vision_workflow.display import (
        active_baseline,
        get_display_info,
        match_scales,
        template_scale,
    )
    from vision_workflow.settings import get_match_settings

    cfg = reload_settings()
    match_cfg = get_match_settings()
    disp = get_display_info()
    scale = template_scale(disp)
    scales = match_scales(scale)
    console.print(f"[bold]vision-workflow[/bold] v{__version__}")
    console.print(f"env       : {cfg.app.get('env')}")
    console.print(f"log_level : {cfg.logging.level}")
    console.print(f"root_dir  : {cfg.root_dir}")
    console.print(f"workflow  : {WORKFLOW.id} ({WORKFLOW.display_name})")
    console.print(active_baseline().format_line(prefix="baseline "))
    console.print(disp.format_line(prefix="current  "))
    console.print(
        f"match     : baseline={match_cfg.baseline_label()} "
        f"multi={'on' if match_cfg.multi_scale else 'off'} "
        f"[{match_cfg.scale_min:g}, {match_cfg.scale_max:g}] "
        f"samples={match_cfg.scale_samples}"
    )
    console.print(f"img_scale : {scale:.4f} → {[round(s, 4) for s in scales]}")


@app.command("version")
def version_cmd() -> None:
    console.print(__version__)


if __name__ == "__main__":
    app()
