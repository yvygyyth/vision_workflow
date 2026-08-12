# vision-workflow

三级组合：**模块 → 流程 → 工作流**。桌面 UI 可干跑 / 运行 / 停止，并可打包成 exe。

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

## 模块

```python
Module(
    id="click_email",
    event=click("data/samples/email.png"),
    success="one_click",
    # fail 省略 → 结束当前流程
)
```

## 目录

```text
config/flow/                # 工作流包（仍用 config.flow 加载）
  __init__.py               # WORKFLOW 聚合
  mail/                     # 一个子流程一个文件夹
  wrap_up/
  handle_fail/
data/samples/               # 模板图
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

界面：工作流名称、流程下拉（按 `name`）、干跑、运行、停止、日志、状态。

## 打包 exe

```powershell
pip install -e ".[dev]"
poe build
```

产物：`dist/VisionWorkflow/VisionWorkflow.exe`，同级带 `config/`、`data/`（可直接改配置再开软件）。

## CLI

```powershell
poe dry
poe flow
vision-workflow flow config.flow --dry-run
```

## 安装

```powershell
pip install -e ".[dev]"
```
