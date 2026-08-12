"""模块组成流程，流程组成工作流。"""

from config.actions import action_handle_fail, action_log_done
from vision_workflow.events import click
from vision_workflow.module import END, Flow, Module, Workflow

# --- 流程 1：收邮件 ---
mail_flow = Flow(
    id="mail",
    entry="click_email",
    modules=[
        Module(
            id="click_email",
            event=click("data/samples/email.png"),
            success="one_click",
            # fail 省略 → 结束当前流程
        ),
        Module(
            id="one_click",
            event=click("data/samples/email_one_click_receive.png"),
            success="space_click",
            fail="click_email",  # 失败可跳回其它模块
        ),
        Module(
            id="space_click",
            event=click("data/samples/space-close.png"),
            success=END
        ),
    ],
    success="wrap_up",  # 本流程成功 → 下一个流程
    # fail 省略 → 结束整个工作流
)

# --- 流程 2：收尾 ---
wrap_up_flow = Flow(
    id="wrap_up",
    entry="done",
    modules=[
        Module(id="done", event=action_log_done, success=END),
    ],
    success=END,
)

# --- 失败处理流程（可选，在其它流程 fail= 时引用）---
fail_flow = Flow(
    id="handle_fail",
    entry="report",
    modules=[
        Module(id="report", event=action_handle_fail, success=END),
    ],
    success=END,
)

FLOWS = [mail_flow, wrap_up_flow, fail_flow]
ENTRY = "mail"

WORKFLOW = Workflow(
    id="main",
    name="config.flow",
    flows=FLOWS,
    entry=ENTRY,
)
