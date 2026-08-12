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

## 延迟与 config

执行后延迟（进入下一项之前）：

- 全局默认：模块之间 **100ms**，流程之间 **200ms**（`Workflow.module_delay_ms` / `flow_delay_ms`）
- 单个模块 / 流程可用 `config={"delay_ms": N}` 覆盖；`0` 表示不延迟

```python
Module(id="a", event=..., success="b", config={"delay_ms": 300})
Flow(id="mail", ..., config={"delay_ms": 500})
Workflow(..., module_delay_ms=100, flow_delay_ms=200)
```

`config` 还可放其它扩展属性。

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
