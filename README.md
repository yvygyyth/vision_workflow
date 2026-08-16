# vision-workflow

三级组合：**模块 → 流程 → 工作流**。桌面 UI 可运行 / 停止，并可打包成 exe。

```text
Module  最小节点：id + event + on（可能性 → 处理函数）
Flow    模块组成的一段流程
Workflow 流程组成的复杂流程
```

## 流程名

```python
from vision_workflow.module import Flow, FlowNode, Workflow
from vision_workflow.status import FULFILLED, REJECTED, EventStatus, FlowStatus

Flow(id="mail", name="收邮件", entry="click_email", modules=[...])
Workflow(
    id="main",
    name="名将杀免费资源每日领取",
    entry="mail",
    nodes=[FlowNode(mail), FlowNode(dang_qing_ge)],  # router 可选
)
```

`name` 给 UI / 日志展示；不填则回退为 `id`。`FlowNode.router` 缺省时：`fulfilled`→顺序下一个，`rejected`→结束（None）。

## 固定枚举（`vision_workflow.status`）

```python
EventStatus.FULFILLED / REJECTED  # 事件方法返回（别名 FULFILLED / REJECTED）
FlowStatus.FULFILLED / REJECTED   # 流程对外状态（FlowRouter）
# 下一跳：业务 id；None = 本层结束（默认接口：成功→下一个，失败→结束）
```

自定义模块结果仍可用普通 str（如 `"loop"`）；核心值请用枚举，避免硬编码字符串。

## 延迟 / 重试（洋葱中间件）

各级 `config` 均为独立类型（悬停即可查看字段）：`ModuleConfig` / `FlowConfig` / `WorkflowConfig`。

```text
Resolve+Delay → Retry → Event
```

```python
from vision_workflow.module import ModuleConfig, FlowConfig, WorkflowConfig, Module, Flow, Workflow
from vision_workflow.status import FULFILLED, REJECTED

Module(
    id="one_click",
    event=...,
    on={FULFILLED: onward, REJECTED: to("click_email")},
    config=ModuleConfig(retry=2, retry_on=[REJECTED], retry_delay_ms=200, delay_ms=100),
)
Flow(id="mail", ..., config=FlowConfig(delay_ms=500))
Workflow(..., config=WorkflowConfig(delay_ms=100))  # start_delay_ms 默认 DEFAULT_START_DELAY_MS（2s）
```

## 模块

`event` 必须返回 `on` 里的某个 key（`EventStatus` 或自定义 str），否则报错并结束当前流程。`on[key]` 返回下一模块 id；`None` 表示本流程结束。

```python
from vision_workflow.events import click
from vision_workflow.module import Module, abort, onward, to
from vision_workflow.status import FULFILLED, REJECTED

Module(
    id="click_email",
    event=click().image("data/ming_jiang_sha/mail/email.png").execute(),
    on={FULFILLED: onward, REJECTED: abort},  # onward=下一模块；abort=结束本流程（配合 REJECTED）
)
Module(
    id="one_click",
    event=...,
    on={FULFILLED: onward, REJECTED: to("click_email")},  # 未找到则跳回
)
# 自循环示例：on={"loop": lambda m: m.again(), FULFILLED: onward}
# 识图后点击：do(move().image("x.png"), click())
# 识图后相对偏移再点：do(move().image("x.png"), move().by(0, 100), click())
# 滚轮：do(move().at("center"), scroll(-8))
# 关弹窗 / 返回：from vision_workflow.actions.ming_jiang_sha import space_close, go_back
```

`ModuleContext` 透传识图 / 鼠标 / 日志，并提供 `next` / `goto` / `again` / `end` / `fail`，方便以后扩展。

## 目录

```text
data/ming_jiang_sha/<流程id>/              # 模板图（打包后在 exe 旁，可热更）
src/vision_workflow/
  flows/
    __init__.py                     # WORKFLOWS 目录注册
    parts/                          # Flow 积木（内部编排）
    workflows/                      # 一目录一个复杂流程
      main/                         # 名将杀免费资源每日领取
  module.py / events.py / flow/
  ui/
scripts/build_exe.py
```

## 桌面 UI

```powershell
poe ui
# 或
vision-workflow ui
python -m vision_workflow.ui
```

界面：复杂流程下拉（按 `Workflow.name`）、运行、停止、日志、状态。用户只选择并执行复杂流程；Flow / Module 为内部编排。

## 打包 exe

```powershell
pip install -e ".[dev]"
poe build
```

产物：`dist/VisionWorkflow/VisionWorkflow.exe`；流程已打进程序，同级仅带 `data/`（模板图可直接改）。

## CLI

```powershell
poe flow
vision-workflow flow
vision-workflow flow -s mail
```

## 安装

```powershell
pip install -e ".[dev]"
```
