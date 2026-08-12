# vision-workflow

三级组合：**模块 → 流程 → 工作流**。桌面 UI 可运行 / 停止，并可打包成 exe。

```text
Module  最小节点：id + event + on（可能性 → 处理函数）
Flow    模块组成的一段流程
Workflow 流程组成的复杂流程
```

## 流程名

```python
Flow(id="mail", name="收邮件", entry="click_email", modules=[...])
Workflow(id="main", name="邮箱一键领取", entry="mail", flows=[...])
```

`name` 给 UI / 日志展示；不填则回退为 `id`。

## 延迟 / 重试（洋葱中间件）

各级 `config` 均为独立类型（悬停即可查看字段）：`ModuleConfig` / `FlowConfig` / `WorkflowConfig`。

```text
Resolve+Delay → Retry → Event
```

```python
from vision_workflow.module import ModuleConfig, FlowConfig, WorkflowConfig, Module, Flow, Workflow

Module(
    id="one_click",
    event=...,
    on={OK: onward, MISS: to("click_email")},
    config=ModuleConfig(retry=2, retry_on=[MISS], retry_delay_ms=200, delay_ms=100),
)
Flow(id="mail", ..., config=FlowConfig(delay_ms=500))
Workflow(..., config=WorkflowConfig(delay_ms=100))  # 模块/流程未写 delay_ms 时的默认
```

## 模块

`event` 必须返回 `on` 里的某个 key，否则报错并结束当前流程。`on[key]` 是处理函数，拿到完整 `ModuleContext`，返回下一模块 id（或 `END` / `FAIL`）。

```python
from vision_workflow.module import MISS, OK, Module, abort, onward, to

Module(
    id="click_email",
    event=click("data/samples/mail/email.png"),
    on={OK: onward, MISS: abort},  # onward=下一模块；abort=失败结束本流程
)
Module(
    id="one_click",
    event=...,
    on={OK: onward, MISS: to("click_email")},  # 未找到则跳回
)
# 自循环示例：on={"loop": lambda m: m.again(), OK: onward}
```

`ModuleContext` 透传识图 / 鼠标 / 日志，并提供 `next` / `goto` / `again` / `end` / `fail`，方便以后扩展。

## 目录

```text
data/samples/<流程id>/              # 模板图（打包后在 exe 旁，可热更）
src/vision_workflow/
  flows/
    __init__.py                     # WORKFLOWS 目录注册
    parts/                          # Flow 积木（内部编排）
    workflows/                      # 一目录一个复杂流程
      main/                         # 邮箱一键领取
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
