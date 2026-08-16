# apps 目录重构 Implementation Plan

> **For agentic workers:** 按任务顺序执行；每步可独立验证。

**Goal:** 将名将杀业务迁入 `apps/ming_jiang_sha/`，删除旧 `flows/` 与 `actions/`。

**Architecture:** 框架留在包根；应用代码按 `common` / `parts` / `workflows` 分层；`apps/__init__.py` 作为 WORKFLOWS 注册入口。

**Tech Stack:** Python 包迁移、import 重写、pytest

## Global Constraints

- 包名用 `apps`，不用 `games`
- 不向后兼容，不留旧路径 re-export
- `data/ming_jiang_sha` 路径布局不变

---

### Task 1: 建立 `apps/ming_jiang_sha/common`

- [ ] 迁入 `paths.py`、原 `actions/ming_jiang_sha/*` → `common/actions/`
- [ ] 修正包内 import 为 `vision_workflow.apps.ming_jiang_sha.common...`

### Task 2: 迁入 parts / workflows

- [ ] 迁入全部 parts 与 workflows
- [ ] parts 改引用 `common.actions`；workflows 改引用 `parts`

### Task 3: 注册入口与调用方

- [ ] 写 `apps/ming_jiang_sha/__init__.py`、`apps/__init__.py`
- [ ] `cli.py` / `ui` 改为 `from vision_workflow.apps import ...`
- [ ] 更新 README 目录说明

### Task 4: 删除旧包并验证

- [ ] 删除 `flows/`、`actions/`
- [ ] `pytest` 通过；全库无旧 import 残留
