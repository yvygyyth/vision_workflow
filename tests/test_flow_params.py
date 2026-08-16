"""Flow / FlowNode params 合并进上下文。"""

from vision_workflow.flow import WorkflowRunner
from vision_workflow.module import Flow, FlowNode, Module, Workflow, onward
from vision_workflow.status import FULFILLED


def test_flow_params_default_and_node_override() -> None:
    seen: dict = {}

    def event(m):
        seen["params"] = dict(m.params)
        return FULFILLED

    flow = Flow(
        id="f",
        entry="a",
        params={"wu_jiang": "张飞", "count": 1},
        modules=[
            Module(id="a", event=event, on={FULFILLED: onward}),
        ],
    )
    workflow = Workflow(
        id="w",
        config={"start_delay_ms": 0},
        nodes=[
            FlowNode(flow, params={"wu_jiang": "关羽"}),
        ],
    )
    result = WorkflowRunner(workflow).run()
    assert result.success
    assert seen["params"] == {"wu_jiang": "关羽", "count": 1}


def test_flow_params_without_node_override() -> None:
    seen: dict = {}

    def event(m):
        seen["params"] = dict(m.params)
        return FULFILLED

    flow = Flow(
        id="f",
        entry="a",
        params={"x": 1},
        modules=[Module(id="a", event=event, on={FULFILLED: onward})],
    )
    workflow = Workflow(
        id="w",
        config={"start_delay_ms": 0},
        nodes=[FlowNode(flow)],
    )
    assert WorkflowRunner(workflow).run().success
    assert seen["params"] == {"x": 1}
