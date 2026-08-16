"""Module / Flow / Workflow 测试。"""

from unittest.mock import patch

from vision_workflow.flow import WorkflowRunner
from vision_workflow.module import (
    DEFAULT_START_DELAY_MS,
    Flow,
    FlowConfig,
    FlowNode,
    FlowRouter,
    Module,
    ModuleConfig,
    Workflow,
    WorkflowConfig,
    abort,
    onward,
    to,
)
from vision_workflow.status import FULFILLED, REJECTED, EventStatus, FlowStatus


def _wf(
    *flows: Flow,
    entry: str | None = None,
    routers: dict[str, FlowRouter] | None = None,
) -> Workflow:
    routers = routers or {}
    return Workflow(
        id="w",
        entry=entry or flows[0].id,
        nodes=[FlowNode(f, router=routers.get(f.id)) for f in flows],
        config=WorkflowConfig(start_delay_ms=0),
    )


def test_module_on_defaults_to_next() -> None:
    workflow = _wf(
        Flow(
            id="f",
            entry="a",
            modules=[
                Module(id="a", event=lambda m: FULFILLED, on={FULFILLED: onward}),
                Module(id="b", event=lambda m: FULFILLED, on={FULFILLED: onward}),
                Module(id="c", event=lambda m: FULFILLED, on={FULFILLED: onward}),
            ],
        )
    )
    result = WorkflowRunner(workflow).run()
    assert result.success
    assert result.path == ["f.a", "f.b", "f.c"]

    workflow = _wf(
        Flow(
            id="f",
            entry="a",
            modules=[
                Module(id="a", event=lambda m: FULFILLED, on={FULFILLED: to("b")}),
                Module(
                    id="b",
                    event=lambda m: FULFILLED,
                    on={FULFILLED: lambda m: m.end()},
                ),
            ],
        )
    )
    result = WorkflowRunner(workflow).run()
    assert result.success
    assert result.path == ["f.a", "f.b"]


def test_module_unknown_key_ends_flow() -> None:
    workflow = _wf(
        Flow(
            id="f",
            entry="a",
            modules=[
                Module(
                    id="a",
                    event=lambda m: "nope",
                    on={FULFILLED: to("b")},
                ),
                Module(id="b", event=lambda m: FULFILLED, on={FULFILLED: onward}),
            ],
        )
    )
    result = WorkflowRunner(workflow).run()
    assert not result.success
    assert result.path == ["f.a"]


def test_module_miss_abort_ends_flow() -> None:
    def event(m):
        m.reason = "识图未找到 [confirm.png]"
        return REJECTED

    workflow = _wf(
        Flow(
            id="f",
            entry="a",
            modules=[
                Module(
                    id="a",
                    name="购买",
                    event=event,
                    on={FULFILLED: to("b"), REJECTED: abort},
                ),
                Module(id="b", event=lambda m: FULFILLED, on={FULFILLED: onward}),
            ],
        )
    )
    result = WorkflowRunner(workflow).run()
    assert not result.success
    assert result.path == ["f.a"]
    assert "识图未找到 [confirm.png]" in (result.feedback or "")
    assert "购买" in (result.feedback or "")


def test_flow_compose_to_workflow_default_order() -> None:
    workflow = _wf(
        Flow(
            id="mail",
            entry="a",
            modules=[Module(id="a", event=lambda m: FULFILLED, on={FULFILLED: onward})],
        ),
        Flow(
            id="done_flow",
            entry="d",
            modules=[Module(id="d", event=lambda m: FULFILLED, on={FULFILLED: onward})],
        ),
    )
    result = WorkflowRunner(workflow).run()
    assert result.success
    assert result.path == ["mail.a", "done_flow.d"]
    assert workflow.router_for("mail").on[FlowStatus.FULFILLED] == "done_flow"
    assert workflow.router_for("mail").on[FlowStatus.REJECTED] is None


def test_flow_rejected_jumps_via_router() -> None:
    workflow = _wf(
        Flow(
            id="mail",
            entry="a",
            modules=[
                Module(
                    id="a",
                    event=lambda m: REJECTED,
                    on={FULFILLED: onward, REJECTED: abort},
                )
            ],
        ),
        Flow(
            id="handle_fail",
            entry="h",
            modules=[
                Module(
                    id="h",
                    event=lambda m: FULFILLED,
                    on={FULFILLED: onward},
                )
            ],
        ),
        routers={
            "mail": FlowRouter(
                on={
                    FlowStatus.FULFILLED: None,
                    FlowStatus.REJECTED: "handle_fail",
                }
            )
        },
    )
    result = WorkflowRunner(workflow).run()
    assert result.path == ["mail.a", "handle_fail.h"]
    assert not result.success


def test_run_single_module() -> None:
    workflow = _wf(
        Flow(
            id="f",
            entry="a",
            modules=[Module(id="a", event=lambda m: FULFILLED, on={FULFILLED: onward})],
        )
    )
    settled = WorkflowRunner(workflow).run_module("a")
    assert settled.ok
    assert settled.status is EventStatus.FULFILLED


def test_dynamic_outcome_jump() -> None:
    workflow = _wf(
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
                Module(id="b", event=lambda m: FULFILLED, on={FULFILLED: onward}),
            ],
        )
    )
    result = WorkflowRunner(workflow).run()
    assert result.path == ["f.a", "f.b"]


def test_self_loop_again() -> None:
    hits = {"n": 0}

    def event(m):
        hits["n"] += 1
        return "loop" if hits["n"] < 3 else FULFILLED

    workflow = _wf(
        Flow(
            id="f",
            entry="a",
            modules=[
                Module(
                    id="a",
                    event=event,
                    on={
                        "loop": lambda m: m.again(),
                        FULFILLED: onward,
                    },
                ),
            ],
        )
    )
    result = WorkflowRunner(workflow).run()
    assert result.success
    assert hits["n"] == 3
    assert result.path == ["f.a", "f.a", "f.a"]


def test_config_workflow_load() -> None:
    from vision_workflow.apps import WORKFLOW, WORKFLOWS, workflow_choices

    wf = WORKFLOW
    assert wf.entry == "mail"
    assert wf.display_name == "名将杀免费资源每日领取"
    assert {f.id for f in wf.flows} >= {"mail", "dang_qing_ge"}
    assert len(wf.nodes) >= 4
    mail = wf.get("mail")
    assert mail.display_name == "收邮件"
    assert mail.entry == "click_email"
    assert set(mail.get("click_email").on) >= {FULFILLED, REJECTED}
    assert mail.default_next_for("click_email") == "one_click"
    assert callable(mail.get("one_click").on[REJECTED])
    dqg = wf.get("dang_qing_ge")
    assert dqg.display_name == "丹青阁"
    assert dqg.entry == "icon"
    assert dqg.default_next_for("icon") == "day_libao"
    assert isinstance(mail.get("click_email").config, ModuleConfig)
    assert isinstance(wf.get("mail").config, FlowConfig)
    assert wf.router_for("mail").on[FlowStatus.FULFILLED] == "dang_qing_ge"
    assert len(WORKFLOWS) >= 1
    assert WORKFLOWS[0].id == "daily_free_resources"
    assert ("名将杀免费资源每日领取", "daily_free_resources") in workflow_choices()


def test_module_retry_on_miss() -> None:
    hits = {"n": 0}

    def flaky(m):
        hits["n"] += 1
        if hits["n"] < 3:
            return REJECTED
        return FULFILLED

    workflow = _wf(
        Flow(
            id="f",
            entry="a",
            modules=[
                Module(
                    id="a",
                    event=flaky,
                    on={FULFILLED: onward, REJECTED: abort},
                    config=ModuleConfig(retry=2, retry_on=[REJECTED]),
                ),
            ],
        )
    )
    result = WorkflowRunner(workflow).run()
    assert result.success
    assert hits["n"] == 3
    assert result.path == ["f.a"]


def test_module_and_flow_config_delay() -> None:
    sleeps: list[float] = []

    workflow = _wf(
        Flow(
            id="f1",
            entry="a",
            modules=[
                Module(
                    id="a",
                    event=lambda m: FULFILLED,
                    on={FULFILLED: to("b")},
                    config=ModuleConfig(delay_ms=30),
                ),
                Module(id="b", event=lambda m: FULFILLED, on={FULFILLED: onward}),
            ],
            config=FlowConfig(delay_ms=40),
        ),
        Flow(
            id="f2",
            entry="c",
            modules=[Module(id="c", event=lambda m: FULFILLED, on={FULFILLED: onward})],
        ),
    )

    def _spy(seconds: float) -> None:
        sleeps.append(seconds)

    with patch("vision_workflow.middleware.time.sleep", side_effect=_spy):
        result = WorkflowRunner(workflow).run()
    assert result.success
    assert result.path == ["f1.a", "f1.b", "f2.c"]
    assert sleeps == [0.03, 0.04]


def test_workflow_start_delay_ms() -> None:
    assert WorkflowConfig().start_delay_ms == DEFAULT_START_DELAY_MS
    sleeps: list[float] = []
    workflow = _wf(
        Flow(
            id="f",
            entry="a",
            modules=[Module(id="a", event=lambda m: FULFILLED, on={FULFILLED: onward})],
        )
    )
    workflow.config = WorkflowConfig(start_delay_ms=120)

    def _spy(seconds: float) -> None:
        sleeps.append(seconds)

    with patch("vision_workflow.flow.runner.time.sleep", side_effect=_spy):
        result = WorkflowRunner(workflow).run()
    assert result.success
    assert result.path == ["f.a"]
    assert abs(sum(sleeps) - 0.12) < 1e-9


def test_config_dict_coercion() -> None:
    mod = Module(
        id="a",
        event=lambda m: FULFILLED,
        on={FULFILLED: onward},
        config={"delay_ms": 10, "retry": 1},  # type: ignore[arg-type]
    )
    assert isinstance(mod.config, ModuleConfig)
    assert mod.config.delay_ms == 10
    assert mod.config.retry == 1


def test_outcome_string_coerces_to_enum() -> None:
    mod = Module(
        id="a",
        event=lambda m: "fulfilled",
        on={"fulfilled": onward, "rejected": abort},
    )
    assert EventStatus.FULFILLED in mod.on
    assert EventStatus.REJECTED in mod.on
    assert mod.has_outcome("fulfilled")
    assert mod.has_outcome(FULFILLED)


def test_flow_loop_via_router() -> None:
    hits = {"n": 0}

    def event(m):
        hits["n"] += 1
        return FULFILLED if hits["n"] < 3 else REJECTED

    f = Flow(
        id="loop_flow",
        entry="a",
        modules=[Module(id="a", event=event, on={FULFILLED: onward, REJECTED: abort})],
    )
    workflow = Workflow(
        id="w",
        nodes=[
            FlowNode(
                f,
                router=FlowRouter(
                    on={
                        FlowStatus.FULFILLED: "loop_flow",
                        FlowStatus.REJECTED: None,
                    }
                ),
            )
        ],
        config=WorkflowConfig(start_delay_ms=0),
    )
    result = WorkflowRunner(workflow).run()
    assert hits["n"] == 3
    assert result.path == ["loop_flow.a", "loop_flow.a", "loop_flow.a"]
    assert not result.success


def test_custom_flow_outcome_routes_next_flow() -> None:
    """流程结束时可用自定义 str/Enum 作为 FlowRouter key。"""
    from enum import Enum

    class Exit(str, Enum):
        SIDE = "side"

    workflow = _wf(
        Flow(
            id="main",
            entry="a",
            modules=[
                Module(
                    id="a",
                    event=lambda m: Exit.SIDE,
                    on={Exit.SIDE: lambda m: m.end()},
                )
            ],
        ),
        Flow(
            id="side",
            entry="b",
            modules=[
                Module(id="b", event=lambda m: FULFILLED, on={FULFILLED: onward}),
            ],
        ),
        routers={
            "main": FlowRouter(
                on={
                    Exit.SIDE: "side",
                    FlowStatus.FULFILLED: None,
                    FlowStatus.REJECTED: None,
                }
            )
        },
    )
    result = WorkflowRunner(workflow).run()
    assert result.success
    assert result.path == ["main.a", "side.b"]
