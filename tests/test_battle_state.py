"""Workflow lifecycle 管局内状态；Flow lifecycle 仍可用。"""

from vision_workflow.apps.ming_jiang_sha.parts.qian_li_dan_qi.utils import (
    VARS_KEY,
    RewardKind,
    bind_battle_state,
    clear_battle_state,
    ensure_battle_state,
    get_battle_state,
)
from vision_workflow.flow import WorkflowRunner
from vision_workflow.module import (
    Flow,
    FlowNode,
    FlowRouter,
    Module,
    Workflow,
    WorkflowConfig,
    WorkflowLifecycle,
    onward,
)
from vision_workflow.status import FULFILLED, REJECTED, FlowStatus


def test_workflow_lifecycle_manages_battle_state() -> None:
    seen: dict = {}

    def select_event(m):
        state = get_battle_state(m.ctx)
        state.copper_coins = 42
        state.mark_general_reward("吕布", RewardKind.TOKEN)
        seen["select"] = True
        return FULFILLED

    def fight_event(m):
        state = get_battle_state(m.ctx)
        seen["fight_copper"] = state.copper_coins
        seen["fight_rewards"] = {
            name: set(kinds) for name, kinds in state.general_rewards.items()
        }
        return FULFILLED

    select = Flow(
        id="battle_select",
        entry="a",
        modules=[Module(id="a", event=select_event, on={FULFILLED: onward})],
    )
    fight = Flow(
        id="fight",
        entry="b",
        modules=[Module(id="b", event=fight_event, on={FULFILLED: onward})],
    )
    workflow = Workflow(
        id="w",
        config=WorkflowConfig(start_delay_ms=0),
        lifecycle=WorkflowLifecycle(
            on_enter=bind_battle_state,
            on_exit=clear_battle_state,
        ),
        nodes=[
            FlowNode(
                select,
                router=FlowRouter(on={FlowStatus.FULFILLED: "fight"}),
            ),
            FlowNode(fight),
        ],
    )
    runner = WorkflowRunner(workflow)
    assert runner.run().success
    assert seen["select"] is True
    assert seen["fight_copper"] == 42
    assert seen["fight_rewards"] == {"吕布": {RewardKind.TOKEN}}
    assert VARS_KEY not in runner.ctx.vars


def test_ensure_does_not_reset_existing_state() -> None:
    from pathlib import Path

    from vision_workflow.flow.context import FlowContext

    ctx = FlowContext(base_dir=Path("."))
    first = ensure_battle_state(ctx)
    first.copper_coins = 7
    second = ensure_battle_state(ctx)
    assert second is first
    assert second.copper_coins == 7


def test_workflow_lifecycle_on_exit_runs_on_reject() -> None:
    exited: list[bool] = []

    flow = Flow(
        id="f",
        entry="a",
        modules=[
            Module(id="a", event=lambda m: REJECTED, on={REJECTED: onward}),
        ],
    )
    workflow = Workflow(
        id="w",
        config=WorkflowConfig(start_delay_ms=0),
        lifecycle={"on_exit": lambda ctx: exited.append(True)},
        nodes=[FlowNode(flow)],
    )
    result = WorkflowRunner(workflow).run()
    assert not result.success
    assert exited == [True]
