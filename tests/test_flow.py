"""组合式模块跳转测试。"""

from pathlib import Path

from vision_workflow.flow import FlowRunner, load_flow_module
from vision_workflow.module import END, FAIL, Module, ModuleGraph
from vision_workflow.promise import Settled


def test_module_jump_success() -> None:
    graph = ModuleGraph(
        name="t",
        entry="a",
        dry_run=True,
        modules=[
            Module(
                id="a",
                action=lambda ctx: True,
                judge=lambda ctx, v: True,
                success="b",
                fail=FAIL,
            ),
            Module(
                id="b",
                action=lambda ctx: ctx.log("b") or True,
                success=END,
                fail=FAIL,
            ),
        ],
    )
    result = FlowRunner(graph).run()
    assert result.success
    assert result.path == ["a", "b"]


def test_module_jump_fail_to_handler() -> None:
    graph = ModuleGraph(
        name="t",
        entry="a",
        dry_run=True,
        modules=[
            Module(
                id="a",
                action=lambda ctx: True,
                judge=lambda ctx, v: False,
                success="b",
                fail="err",
            ),
            Module(
                id="b",
                action=lambda ctx: True,
                success=END,
            ),
            Module(
                id="err",
                action=lambda ctx: Settled.resolve("handled", feedback="handled"),
                success=END,
                fail=FAIL,
            ),
        ],
    )
    result = FlowRunner(graph).run()
    assert result.success
    assert result.path == ["a", "err"]


def test_run_single_module() -> None:
    graph = ModuleGraph(
        name="t",
        entry="a",
        dry_run=True,
        modules=[Module(id="a", action=lambda ctx: 1, success=END)],
    )
    settled = FlowRunner(graph).run_module("a")
    assert settled.ok


def test_dynamic_success_jump() -> None:
    graph = ModuleGraph(
        name="t",
        entry="a",
        dry_run=True,
        modules=[
            Module(
                id="a",
                action=lambda ctx: "go-b",
                success=lambda ctx, v: "b" if v == "go-b" else END,
                fail=FAIL,
            ),
            Module(id="b", action=lambda ctx: True, success=END),
        ],
    )
    result = FlowRunner(graph).run()
    assert result.path == ["a", "b"]


def test_config_modules_load() -> None:
    import sys

    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    flow = load_flow_module("config.flow")
    assert flow.entry == "click_email"
    assert {m.id for m in flow.modules} >= {"click_email", "done", "handle_fail"}
