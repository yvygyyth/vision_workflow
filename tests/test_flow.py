"""Module / Flow / Workflow 测试。"""

from pathlib import Path

from vision_workflow.flow import FlowRunner, load_flow_module
from vision_workflow.module import END, Flow, Module, Workflow
from vision_workflow.promise import Settled


def test_module_jump_inside_flow() -> None:
    workflow = Workflow(
        id="w",
        entry="f",
        dry_run=True,
        flows=[
            Flow(
                id="f",
                entry="a",
                modules=[
                    Module(id="a", event=lambda ctx: True, success="b"),
                    Module(id="b", event=lambda ctx: ctx.log("b") or True, success=END),
                ],
                success=END,
            )
        ],
    )
    result = FlowRunner(workflow).run()
    assert result.success
    assert result.path == ["f.a", "f.b"]


def test_module_fail_defaults_end_flow() -> None:
    workflow = Workflow(
        id="w",
        entry="f",
        dry_run=True,
        flows=[
            Flow(
                id="f",
                entry="a",
                modules=[
                    Module(
                        id="a",
                        event=lambda ctx: Settled.reject("x", feedback="x"),
                        success="b",
                        # fail 默认结束流程
                    ),
                    Module(id="b", event=lambda ctx: True, success=END),
                ],
                success=END,
            )
        ],
    )
    result = FlowRunner(workflow).run()
    assert not result.success
    assert result.path == ["f.a"]


def test_flow_compose_to_workflow() -> None:
    workflow = Workflow(
        id="w",
        entry="mail",
        dry_run=True,
        flows=[
            Flow(
                id="mail",
                entry="a",
                modules=[Module(id="a", event=lambda ctx: True, success=END)],
                success="done_flow",
            ),
            Flow(
                id="done_flow",
                entry="d",
                modules=[Module(id="d", event=lambda ctx: True, success=END)],
                success=END,
            ),
        ],
    )
    result = FlowRunner(workflow).run()
    assert result.success
    assert result.path == ["mail.a", "done_flow.d"]


def test_flow_fail_jumps_to_handler_flow() -> None:
    workflow = Workflow(
        id="w",
        entry="mail",
        dry_run=True,
        flows=[
            Flow(
                id="mail",
                entry="a",
                modules=[
                    Module(
                        id="a",
                        event=lambda ctx: Settled.reject("boom", feedback="boom"),
                        success=END,
                    )
                ],
                success=END,
                fail="handle_fail",
            ),
            Flow(
                id="handle_fail",
                entry="h",
                modules=[
                    Module(
                        id="h",
                        event=lambda ctx: Settled.resolve("ok", feedback="handled"),
                        success=END,
                    )
                ],
                success=END,
            ),
        ],
    )
    result = FlowRunner(workflow).run()
    assert result.path == ["mail.a", "handle_fail.h"]
    assert not result.success  # 业务路径曾失败


def test_run_single_module() -> None:
    workflow = Workflow(
        id="w",
        entry="f",
        dry_run=True,
        flows=[
            Flow(
                id="f",
                entry="a",
                modules=[Module(id="a", event=lambda ctx: 1, success=END)],
            )
        ],
    )
    settled = FlowRunner(workflow).run_module("a")
    assert settled.ok


def test_dynamic_success_jump() -> None:
    workflow = Workflow(
        id="w",
        entry="f",
        dry_run=True,
        flows=[
            Flow(
                id="f",
                entry="a",
                modules=[
                    Module(
                        id="a",
                        event=lambda ctx: "go-b",
                        success=lambda ctx, v: "b" if v == "go-b" else END,
                    ),
                    Module(id="b", event=lambda ctx: True, success=END),
                ],
                success=END,
            )
        ],
    )
    result = FlowRunner(workflow).run()
    assert result.path == ["f.a", "f.b"]


def test_config_workflow_load() -> None:
    import sys

    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    wf = load_flow_module("config.flow")
    assert wf.entry == "mail"
    assert {f.id for f in wf.flows} >= {"mail", "wrap_up", "handle_fail"}
    mail = wf.get("mail")
    assert mail.entry == "click_email"
    assert mail.get("click_email").success == "one_click"
    assert mail.get("click_email").fail is None
