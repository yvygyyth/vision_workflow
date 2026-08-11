# vision-workflow

组合式平级模块：每个模块有 **id**，跑完自己的生命周期后可跳到任意模块。

## 生命周期

```text
Module(id)
  → action(ctx)          # 做事（可不识图）
    → judge(ctx, value)  # 可选判定函数
    → success / fail     # 下一个模块 id（或函数动态返回）
```

## 目录

```text
config/                 # 你的流程配置（MODULES + ENTRY）
  flow.py
  actions.py
src/vision_workflow/    # 框架：识图、鼠标、模块跳转
data/samples/           # 模板图
```

## 配置（`config/flow.py`）

```python
from vision_workflow.module import END, FAIL, Module

MODULES = [
    Module(
        id="click_email",
        action=action_click_email,
        judge=judge_ok,
        success="done",          # 成功跳转
        fail="handle_fail",      # 失败跳转；写自己的 id 即循环
        max_loops=0,             # 0=不限制本模块循环次数
    ),
    Module(id="done", action=..., success=END),
    Module(id="handle_fail", action=..., success=END, fail=FAIL),
]

ENTRY = "click_email"
```

动态跳转：

```python
success=lambda ctx, value: "module_b" if value else "module_c"
```

## 命令

```powershell
# 查看帮助
vision-workflow --help
vision-workflow flow --help

# 从入口跑（真实点击）
vision-workflow flow config.flow

# 干跑：只识图/规划，不真动鼠标
vision-workflow flow config.flow --dry-run

# 从任意模块开始
vision-workflow flow config.flow -s click_email --dry-run

# 只跑某一个模块生命周期（不跳转）
vision-workflow flow config.flow --only click_email --dry-run

# 运行信息 / 版本
vision-workflow info
vision-workflow version
```

也可用模块方式：`python -m vision_workflow flow config.flow --dry-run`

## 安装

```powershell
pip install -e ".[dev]"
```
