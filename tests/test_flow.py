"""Module / Flow / Workflow 测试。"""

from vision_workflow.flow import WorkflowRunner, load_flow_module
from vision_workflow.module import (
    END,
    MISS,
    OK,
    Flow,
    Module,
    Workflow,
    abort,
    onward,
    resolve_delay_ms,
    to,
)


def test_module_on_defaults_to_next() -> None:
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
                    Module(id="a", event=lambda m: OK, on={OK: onward}),
                    Module(id="b", event=lambda m: OK, on={OK: onward}),
                    Module(id="c", event=lambda m: OK, on={OK: onward}),
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
                    Module(id="a", event=lambda m: OK, on={OK: to("b")}),
                    Module(
                        id="b",
                        event=lambda m: (m.log("b") or OK),
                        on={OK: lambda m: m.end()},
                    ),
                ],
                success=END,
            )
        ],
    )
    result = WorkflowRunner(workflow).run()
    assert result.success
    assert result.path == ["f.a", "f.b"]


def test_module_unknown_key_ends_flow() -> None:
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
                        event=lambda m: "nope",
                        on={OK: to("b")},
                    ),
                    Module(id="b", event=lambda m: OK, on={OK: onward}),
                ],
                success=END,
            )
        ],
    )
    result = WorkflowRunner(workflow).run()
    assert not result.success
    assert result.path == ["f.a"]


def test_module_miss_abort_ends_flow() -> None:
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
                        event=lambda m: MISS,
                        on={OK: to("b"), MISS: abort},
                    ),
                    Module(id="b", event=lambda m: OK, on={OK: onward}),
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
                modules=[Module(id="a", event=lambda m: OK, on={OK: onward})],
                success="done_flow",
            ),
            Flow(
                id="done_flow",
                entry="d",
                modules=[Module(id="d", event=lambda m: OK, on={OK: onward})],
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
                        event=lambda m: MISS,
                        on={OK: onward, MISS: abort},
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
                        event=lambda m: OK,
                        on={OK: onward},
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
                modules=[Module(id="a", event=lambda m: OK, on={OK: onward})],
            )
        ],
    )
    settled = WorkflowRunner(workflow).run_module("a")
    assert settled.ok


def test_dynamic_outcome_jump() -> None:
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
                        event=lambda m: "go-b",
                        on={
                            "go-b": to("b"),
                            "stop": lambda m: m.end(),
                        },
                    ),
                    Module(id="b", event=lambda m: OK, on={OK: onward}),
                ],
                success=END,
            )
        ],
    )
    result = WorkflowRunner(workflow).run()
    assert result.path == ["f.a", "f.b"]


def test_self_loop_again() -> None:
    hits = {"n": 0}

    def event(m):
        hits["n"] += 1
        return "loop" if hits["n"] < 3 else OK

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
                    Module(
                        id="a",
                        event=event,
                        on={
                            "loop": lambda m: m.again(),
                            OK: onward,
                        },
                    ),
                ],
                success=END,
            )
        ],
    )
    result = WorkflowRunner(workflow).run()
    assert result.success
    assert hits["n"] == 3
    assert result.path == ["f.a", "f.a", "f.a"]


def test_config_workflow_load() -> None:
    from vision_workflow.flows import DEFAULT_FLOW_TARGET

    wf = load_flow_module(DEFAULT_FLOW_TARGET)
    assert wf.entry == "mail"
    assert wf.display_name == "邮箱一键领取"
    assert {f.id for f in wf.flows} >= {"mail", "dang_qing_ge", "wrap_up", "handle_fail"}
    mail = wf.get("mail")
    assert mail.display_name == "收邮件"
    assert mail.entry == "click_email"
    assert set(mail.get("click_email").on) >= {OK, MISS}
    assert mail.default_next_for("click_email") == "one_click"
    assert callable(mail.get("one_click").on[MISS])
    assert ("收邮件", "mail") in wf.flow_choices()
    dqg = wf.get("dang_qing_ge")
    assert dqg.display_name == "丹青阁"
    assert dqg.entry == "icon"
    assert dqg.default_next_for("icon") == "day_libao"
    assert ("丹青阁", "dang_qing_ge") in wf.flow_choices()
    assert wf.module_delay_ms == 100
    assert wf.flow_delay_ms == 200


def test_module_retry_on_miss() -> None:
    hits = {"n": 0}

    def flaky(m):
        hits["n"] += 1
        if hits["n"] < 3:
            return MISS
        return OK

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
                    Module(
                        id="a",
                        event=flaky,
                        on={OK: onward, MISS: abort},
                        config={"retry": 2, "retry_on": [MISS]},
                    ),
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
                    Module(
                        id="a",
                        event=lambda m: OK,
                        on={OK: to("b")},
                        config={"delay_ms": 30},
                    ),
                    Module(id="b", event=lambda m: OK, on={OK: onward}),
                ],
                success="f2",
                config={"delay_ms": 40},
            ),
            Flow(
                id="f2",
                entry="c",
                modules=[Module(id="c", event=lambda m: OK, on={OK: onward})],
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
