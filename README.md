# vision-workflow

三级组合：**模块 → 流程 → 工作流**。桌面 UI 可运行 / 停止，并可打包成 exe。

```text
Module  最小节点：id + event + success + fail?
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

`config` 扩展属性，由中间件洋葱处理（不必在 Runner 里堆逻辑）：

```text
Resolve+Delay → Retry → Event
```

| 键 | 含义 |
|----|------|
| `delay_ms` | 成功后、进入下一项前的等待；不写则用 Workflow 全局默认 |
| `retry` | 失败后重试次数；耗尽才算真失败（总尝试 = 1 + retry） |
| `retry_delay_ms` | 两次重试之间的等待 |

```python
Module(
    id="one_click",
    event=...,
    fail="click_email",
    config={"retry": 2, "retry_delay_ms": 200, "delay_ms": 100},
)
Flow(id="mail", ..., config={"retry": 1, "delay_ms": 500})
```

## 模块

```python
Module(id="click_email", event=click("data/samples/mail/email.png"))
# success 省略 → 自动下一个模块；最后一个成功则结束本流程
# fail 省略 → 结束当前流程
Module(id="one_click", event=..., fail="click_email")  # 失败可跳回
```

## 目录

```text
config/flow/                # 工作流包（仍用 config.flow 加载）
  __init__.py               # WORKFLOW 聚合
  mail/                     # 一个子流程一个文件夹
  wrap_up/
  handle_fail/
data/samples/<流程id>/      # 按流程分目录的模板图
src/vision_workflow/
  module.py / events.py / flow/
  ui/                       # 桌面界面（模块化）
    panels/                 # 控制区、日志、状态条
    services/               # 后台执行、日志桥
    window.py / app.py
scripts/build_exe.py        # PyInstaller 打包
```

## 桌面 UI

```powershell
poe ui
# 或
vision-workflow ui
python -m vision_workflow.ui
```

界面：工作流名称、流程下拉（按 `name`）、运行、停止、日志、状态。

## 打包 exe

```powershell
pip install -e ".[dev]"
poe build
```

产物：`dist/VisionWorkflow/VisionWorkflow.exe`，同级带 `config/`、`data/`（可直接改配置再开软件）。

## CLI

```powershell
poe flow
vision-workflow flow config.flow
vision-workflow flow config.flow -s mail
```

## 安装

```powershell
pip install -e ".[dev]"
```
