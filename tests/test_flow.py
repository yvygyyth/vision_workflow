"""Module / Flow / Workflow 测试。"""

from pathlib import Path

from vision_workflow.flow import WorkflowRunner, load_flow_module
from vision_workflow.module import END, Flow, Module, Workflow, resolve_delay_ms
from vision_workflow.promise import Settled


def test_module_success_defaults_to_next() -> None:
    workflow = Workflow(
        id="w",
        entry="f",
        module_delay_ms=0,
        flow_delay_ms=0,
        flows=[
            Flow(
                id="f",
                entry="a",
                modules=[
                    Module(id="a", event=lambda ctx: True),
                    Module(id="b", event=lambda ctx: True),
                    Module(id="c", event=lambda ctx: True),
                ],
                success=END,
            )
        ],
    )
    result = WorkflowRunner(workflow).run()
    assert result.success
    assert result.path == ["f.a", "f.b", "f.c"]

    workflow = Workflow(
        id="w",
        entry="f",
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
    result = WorkflowRunner(workflow).run()
    assert result.success
    assert result.path == ["f.a", "f.b"]


def test_module_fail_defaults_end_flow() -> None:
    workflow = Workflow(
        id="w",
        entry="f",
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
    result = WorkflowRunner(workflow).run()
    assert not result.success
    assert result.path == ["f.a"]


def test_flow_compose_to_workflow() -> None:
    workflow = Workflow(
        id="w",
        entry="mail",
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
    result = WorkflowRunner(workflow).run()
    assert result.success
    assert result.path == ["mail.a", "done_flow.d"]


def test_flow_fail_jumps_to_handler_flow() -> None:
    workflow = Workflow(
        id="w",
        entry="mail",
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
    result = WorkflowRunner(workflow).run()
    assert result.path == ["mail.a", "handle_fail.h"]
    assert not result.success  # 业务路径曾失败


def test_run_single_module() -> None:
    workflow = Workflow(
        id="w",
        entry="f",
        flows=[
            Flow(
                id="f",
                entry="a",
                modules=[Module(id="a", event=lambda ctx: 1, success=END)],
            )
        ],
    )
    settled = WorkflowRunner(workflow).run_module("a")
    assert settled.ok


def test_dynamic_success_jump() -> None:
    workflow = Workflow(
        id="w",
        entry="f",
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
    result = WorkflowRunner(workflow).run()
    assert result.path == ["f.a", "f.b"]


def test_config_workflow_load() -> None:
    import sys

    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    wf = load_flow_module("config.flow")
    assert wf.entry == "mail"
    assert wf.display_name == "邮箱一键领取"
    assert {f.id for f in wf.flows} >= {"mail", "wrap_up", "handle_fail"}
    mail = wf.get("mail")
    assert mail.display_name == "收邮件"
    assert mail.entry == "click_email"
    assert mail.get("click_email").success is None
    assert mail.default_success_for("click_email") == "one_click"
    assert mail.get("click_email").fail is None
    assert ("收邮件", "mail") in wf.flow_choices()
    assert wf.module_delay_ms == 100
    assert wf.flow_delay_ms == 200


def test_module_retry_before_real_fail() -> None:
    hits = {"n": 0}

    def flaky(ctx):
        hits["n"] += 1
        if hits["n"] < 3:
            return Settled.reject("temp", feedback="temp")
        return Settled.resolve(True)

    workflow = Workflow(
        id="w",
        entry="f",
        module_delay_ms=0,
        flow_delay_ms=0,
        flows=[
            Flow(
                id="f",
                entry="a",
                modules=[
                    Module(id="a", event=flaky, config={"retry": 2}),
                ],
                success=END,
            )
        ],
    )
    result = WorkflowRunner(workflow).run()
    assert result.success
    assert hits["n"] == 3
    assert result.path == ["f.a"]


def test_resolve_delay_ms() -> None:
    assert resolve_delay_ms({}, 100) == 100
    assert resolve_delay_ms({"delay_ms": 50}, 100) == 50
    assert resolve_delay_ms({"delay_ms": 0}, 100) == 0


def test_module_and_flow_config_delay() -> None:
    sleeps: list[float] = []

    workflow = Workflow(
        id="w",
        entry="f1",
        module_delay_ms=100,
        flow_delay_ms=200,
        flows=[
            Flow(
                id="f1",
                entry="a",
                modules=[
                    Module(id="a", event=lambda ctx: True, success="b", config={"delay_ms": 30}),
                    Module(id="b", event=lambda ctx: True, success=END),
                ],
                success="f2",
                config={"delay_ms": 40},
            ),
            Flow(
                id="f2",
                entry="c",
                modules=[Module(id="c", event=lambda ctx: True, success=END)],
                success=END,
            ),
        ],
    )
    runner = WorkflowRunner(workflow)
    original = runner.ctx.sleep

    def _spy(seconds: float) -> None:
        sleeps.append(seconds)
        original(seconds)

    runner.ctx.sleep = _spy  # type: ignore[method-assign]
    result = runner.run()
    assert result.success
    assert result.path == ["f1.a", "f1.b", "f2.c"]
    assert sleeps == [0.03, 0.04]  # 模块后 30ms，流程后 40ms
