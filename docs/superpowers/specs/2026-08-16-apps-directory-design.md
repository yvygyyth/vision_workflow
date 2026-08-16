# apps 目录重构设计

**日期:** 2026-08-16  
**状态:** 已确认

## 目标

把名将杀业务从散落的 `flows/parts`、`flows/workflows`、`actions/ming_jiang_sha` 收拢到 `apps/ming_jiang_sha/`，分清三层：

1. **框架公共** — `vision_workflow` 根下（module / events / flow / ui …）
2. **应用专属公共** — `apps/ming_jiang_sha/common/`
3. **应用局部** — `apps/ming_jiang_sha/parts/`、`workflows/`

不向后兼容；删除旧包，不留 re-export。

## 目标结构

```text
src/vision_workflow/
  apps/
    __init__.py                 # 汇总 WORKFLOWS，CLI/UI 唯一入口
    ming_jiang_sha/
      __init__.py               # 本应用 WORKFLOWS
      common/
        paths.py
        actions/                # space_close / go_back / buy / click_*
      parts/                    # 各 Flow
      workflows/                # main / solo
data/ming_jiang_sha/            # 模板资源仍在仓库根
```

## 导入约定

```python
from vision_workflow.apps import WORKFLOWS, get_workflow, workflow_choices
from vision_workflow.apps.ming_jiang_sha.common.actions import go_back, buy
from vision_workflow.apps.ming_jiang_sha.parts.mail import FLOW as mail
```

## 删除

- `src/vision_workflow/flows/`
- `src/vision_workflow/actions/`

## 非目标

- 不改 `data/` 磁盘布局
- 不改 Module / Flow / Workflow 运行时语义
- 不引入多应用热插拔机制（仅预留 `apps/` 目录）
