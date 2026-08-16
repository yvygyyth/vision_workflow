"""Flow lifecycle 与局内状态生命周期。"""

from vision_workflow.apps.ming_jiang_sha.parts.qian_li_dan_qi.battle.state import (
    VARS_KEY,
    bind_battle_state,
    clear_battle_state,
    get_battle_state,
)
from vision_workflow.flow import WorkflowRunner
from vision_workflow.module import (
    Flow,
    FlowLifecycle,
    FlowNode,
    Module,
    Workflow,
    WorkflowConfig,
    onward,
)
from vision_workflow.status import FULFILLED, REJECTED


def test_flow_lifecycle_clears_battle_state() -> None:
    seen: dict = {}

    def event(m):
        state = get_battle_state(m.ctx)
        state.critical_tokens.add("关键信物")
        state.buffs.add("驰援")
        state.copper_coins = 42
        seen["during"] = VARS_KEY in m.ctx.vars
        return FULFILLED

    flow = Flow(
        id="battle",
        entry="a",
        lifecycle=FlowLifecycle(
            on_enter=bind_battle_state,
            on_exit=clear_battle_state,
        ),
        modules=[Module(id="a", event=event, on={FULFILLED: onward})],
    )
    workflow = Workflow(
        id="w",
        config=WorkflowConfig(start_delay_ms=0),
        nodes=[FlowNode(flow)],
    )
    runner = WorkflowRunner(workflow)
    assert runner.run().success
    assert seen["during"] is True
    assert VARS_KEY not in runner.ctx.vars


def test_flow_lifecycle_on_exit_runs_on_reject() -> None:
    exited: list[bool] = []

    flow = Flow(
        id="f",
        entry="a",
        lifecycle={"on_exit": lambda ctx: exited.append(True)},
        modules=[
            Module(id="a", event=lambda m: REJECTED, on={REJECTED: onward}),
        ],
    )
    workflow = Workflow(
        id="w",
        config=WorkflowConfig(start_delay_ms=0),
        nodes=[FlowNode(flow)],
    )
    result = WorkflowRunner(workflow).run()
    assert not result.success
    assert exited == [True]
