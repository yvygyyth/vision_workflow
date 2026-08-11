"""命令行入口。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from vision_workflow import __version__
from vision_workflow.actions import list_actions
from vision_workflow.config import reload_settings
from vision_workflow.logging_utils import setup_logging
from vision_workflow.pipeline import Pipeline
from vision_workflow.recognizers import list_recognizers

# 确保注册表已加载
import vision_workflow.actions.impl  # noqa: F401
import vision_workflow.recognizers.impl  # noqa: F401

app = typer.Typer(
    name="vision-workflow",
    help="配置驱动识图执行流程",
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
    start: Optional[str] = typer.Option(None, "--start", "-s", help="从指定模块 id 开始"),
    only: Optional[str] = typer.Option(None, "--only", help="只执行某一个模块的生命周期（不跳转）"),
    dry_run: bool = typer.Option(False, "--dry-run", help="不真实操作鼠标"),
    base_dir: Optional[Path] = typer.Option(None, "--base-dir", help="模板图相对路径基准目录"),
    json_out: bool = typer.Option(False, "--json", help="JSON 输出"),
) -> None:
    """按模块 id 组合跳转执行流程。"""
    import sys

    from vision_workflow.flow import FlowRunner, load_flow_module
    from vision_workflow.config import reload_settings
    from vision_workflow.logging_utils import setup_logging

    cwd = str(Path.cwd())
    if cwd not in sys.path:
        sys.path.insert(0, cwd)

    setup_logging(reload_settings())
    flow = load_flow_module(target)
    runner = FlowRunner(
        flow,
        base_dir=base_dir,
        dry_run=True if dry_run else None,
        entry=start,
    )
    if only:
        settled = runner.run_module(only)
        if json_out:
            console.print_json(settled.__dict__ if False else {
                "ok": settled.ok,
                "error": settled.error,
                "feedback": settled.feedback,
            })
        else:
            console.print(f"module={only} ok={settled.ok} | {settled.feedback or settled.error}")
        raise typer.Exit(code=0 if settled.ok else 1)

    result = runner.run(start=start)
    if json_out:
        console.print_json(result.model_dump_json())
    else:
        table = Table(title=f"Flow · {result.flow_name}")
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


@app.command("run")
def run_cmd(
    image: Path = typer.Argument(..., exists=True, readable=True, help="待识别图片路径"),
    config: Optional[Path] = typer.Option(None, "--config", "-c", help="配置文件路径"),
    recognizer: Optional[str] = typer.Option(None, "--recognizer", "-r", help="覆盖识图器"),
    dry_run: bool = typer.Option(False, "--dry-run", help="只规划不执行"),
    json_out: bool = typer.Option(False, "--json", help="以 JSON 输出结果"),
) -> None:
    """对单张图片跑完整流水线。"""
    cfg = reload_settings(str(config) if config else None)
    if recognizer:
        cfg.pipeline.recognizer = recognizer
    if dry_run:
        cfg.pipeline.dry_run = True

    setup_logging(cfg)
    pipeline = Pipeline(cfg)
    result = pipeline.run(image)

    if json_out:
        console.print_json(result.model_dump_json())
    else:
        _print_result(result)

    raise typer.Exit(code=0 if result.success else 1)


@app.command("info")
def info_cmd(
    config: Optional[Path] = typer.Option(None, "--config", "-c", help="配置文件路径"),
) -> None:
    """查看当前配置与可用插件。"""
    cfg = reload_settings(str(config) if config else None)
    console.print(f"[bold]vision-workflow[/bold] v{__version__}")
    console.print(f"env           : {cfg.app.get('env')}")
    console.print(f"recognizer    : {cfg.pipeline.recognizer}")
    console.print(f"dry_run       : {cfg.pipeline.dry_run}")
    console.print(f"min_confidence: {cfg.pipeline.min_confidence}")
    console.print(f"recognizers   : {', '.join(list_recognizers())}")
    console.print(f"actions       : {', '.join(list_actions())}")


@app.command("version")
def version_cmd() -> None:
    console.print(__version__)


def _print_result(result) -> None:
    table = Table(title=f"Pipeline Result · {result.run_id}")
    table.add_column("字段", style="cyan")
    table.add_column("值")
    table.add_row("image", result.image_path)
    table.add_row("success", str(result.success))
    table.add_row("message", result.message)
    if result.recognition:
        table.add_row("intent", result.recognition.intent.value)
        table.add_row("confidence", f"{result.recognition.confidence:.2f}")
        table.add_row("text", result.recognition.text[:200])
    if result.plan:
        table.add_row("plan_params", json.dumps(result.plan.params, ensure_ascii=False))
    if result.action:
        table.add_row("action_status", result.action.status.value)
        table.add_row("action_message", result.action.message)
    console.print(table)


if __name__ == "__main__":
    app()
