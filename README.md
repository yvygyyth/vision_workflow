# vision-workflow

三级组合：**模块 → 流程 → 工作流**。

```text
Module  最小节点：id + event + success + fail?
Flow    模块组成的一段流程
Workflow 流程组成的复杂流程
```

## 模块

```python
Module(
    id="click_email",
    event=click("data/samples/email.png"),  # 事件（成功/失败由返回值决定）
    success="one_click",                    # 成功执行什么（下一模块 id / END）
    # fail 省略 → 结束当前流程
    # fail="click_email",                   # 也可跳到其它模块
)
```

没有 `judge`：事件本身返回 `Settled` / 真值即成功，失败即走 `fail`。

## 流程与工作流

```python
mail_flow = Flow(
    id="mail",
    entry="click_email",
    modules=[...],
    success="wrap_up",   # 本流程成功 → 下一个流程
    # fail 省略 → 结束整个工作流
    # fail="handle_fail",
)

WORKFLOW = Workflow(
    id="main",
    entry="mail",
    flows=[mail_flow, wrap_up_flow, fail_flow],
)
```

也可只导出 `FLOWS` + `ENTRY`，或单流程快捷 `MODULES` + `ENTRY`。

## 目录

```text
config/flow.py          # 业务：Module / Flow / Workflow
config/actions.py       # 自定义 event
src/vision_workflow/    # 框架
  module.py             # Module / Flow / Workflow
  events.py             # click 等常用事件
  flow/                 # 运行器
```

## 命令

```powershell
poe dry
poe flow
vision-workflow flow config.flow --dry-run
vision-workflow flow config.flow -s mail
vision-workflow flow config.flow -s mail.click_email --dry-run
vision-workflow flow config.flow --only mail.one_click --dry-run
```

## 安装

```powershell
pip install -e ".[dev]"
```
