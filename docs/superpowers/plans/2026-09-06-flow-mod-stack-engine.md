# Flow-Mod 运行栈引擎 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 按定稿契约重写 runner：return/goto 分轨、沿运行栈 relocate + 去重、去掉 `_resume_after` / 父链特判；不向后兼容。

**Architecture:** 单一 `_flow_stack` 为运行真相；`Result.then`/返回字符串 = return（仅栈内 Flow 或同父兄弟）；`ctx.goto` = 全开跳转（栈外裁到入口再 dispatch，不重建中间帧）；call 内 goto 可 `JumpEscape` 逃出；relocate 成功按 goto。

**Tech Stack:** Python 3、pytest、现有 `vision_bot.runtime`

## Global Constraints

- 不向后兼容；不保留 `_resume_after` / `ThenEscape` 旧语义（可改名为 `JumpEscape`）
- 用户未要求则不 git commit
- 工具 Flow 调度不特殊
- relocate 入口与失败同一套规则

---

### Task 1: 跳转 API 与错误类型

**Files:**
- Modify: `src/vision_bot/runtime/jump.py`
- Modify: `src/vision_bot/runtime/context.py`
- Modify: `src/vision_bot/runtime/result.py`（文档字符串对齐）

**Interfaces:**
- Produces: `JumpEscape(target_id)`, `JumpTargetError`, `ctx.goto(target_id) -> NoReturn`

- [ ] 将 `ThenEscape` 改为 `JumpEscape`（call/goto 逃出当前 drive）
- [ ] `RunContext.goto(id)` 委托 `runner.goto`
- [ ] 文档：`then` 仅成功有效，语义为 return

---

### Task 2: Runner 核心重写（TDD）

**Files:**
- Modify: `src/vision_bot/runtime/runner.py`
- Modify: `tests/test_vision_bot.py`

**行为要点:**
1. `_apply_return(from_id, target)`：目标 ∈ `_flow_stack` 或与 `from_id` 同父兄弟，否则 `JumpTargetError`；裁栈后返回 target 给 trampoline
2. `_apply_goto(target)`：栈内裁到目标；否则最近栈上祖先；否则裁到入口/根；不 push 中间 Flow；若栈深 ≤ 当前 drive floor 则 `raise JumpEscape`
3. 删除 `_resume_after`
4. 失败/入口 relocate：沿 `_flow_stack` 自顶向下，有 `relocate` 且未在 `_relocate_tried` 则试一次；成功清空 tried 并 goto；根失败清空 tried 并 fail
5. `call`：嵌套 drive；`JumpEscape` 向外抛；正常结束回调用方

- [ ] 先改/增测试（见下），再改 runner 至全绿

**关键新测试用例:**
- return 跳兄弟 / 栈内 Flow OK；return 跳叔伯报错
- goto 跨分支 OK；栈外 goto 裁到根再跑目标
- call 内 goto 逃出后不执行 call 后代码
- call 正常仍回调用方
- relocate 沿栈冒泡 + 同 id 本轮不重复；成功后可再 relocate

---

### Task 3: 更新旧测试中的跨树 `then`

- [ ] `test_then_loop_*`、`test_call_tool_flow_*` 等跨父 `then` 改为 `ctx.goto`
- [ ] 同父 `then`（如 a→c）保留

---

### Task 4: 业务代码审计

- [ ] 扫描 apps 下 `then=` / `return "` / `ctx.call`
- [ ] 非兄弟、非栈内的 `then` 改为 `goto` 或报 bug 清单

---

### Task 5: 全量 pytest

- [ ] `pytest tests/test_vision_bot.py -v` 全绿
