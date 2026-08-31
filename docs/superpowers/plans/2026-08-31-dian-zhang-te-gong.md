# 店长特供 Implementation Plan

> **For agentic workers:** 本任务极简，可直接在本会话实现，不必再派 subagent。

**Goal:** 新增异环「店长特供」根流程并挂到 UI 可选列表。

**Architecture:** 新建 `apps/yi_huan`，两步 Module（开始 → 连点至领取），catalog 合并 ROOT_FLOWS。

**Tech Stack:** 现有 `flow`/`mod`、`find`、`move`/`click`/`click_at`。

## Global Constraints

- 素材路径：`data/yi_huan/dian_zhang_te_gong/`
- 点击间隔 0.2s；领取探测间隔 2s
- 探测到领取后要点击再结束

---

### Task 1: 包与步骤

- [ ] 创建 `apps/yi_huan/{__init__,paths,registry}.py`
- [ ] 创建 `dian_zhang_te_gong/{__init__,build,steps}.py`
- [ ] 更新 `runtime/catalog.py` 合并注册
- [ ] 冒烟：`get_root_flow("dian_zhang_te_gong")` 可构建
