# Flow 入参设计

**日期:** 2026-08-16  
**状态:** 已确认并实现

## 模型

- `Flow.params`：硬编码默认参数（`dict`）
- `FlowNode.params`：Workflow 编排时传入（覆盖默认）
- Flow 开跑时合并：`{**flow.params, **node.params}`（传入优先）
- 结果写入 `FlowContext.params`，Module 经 `m.params` 读取

## 非目标

- 不使用 JSON 字符串作为主 API
- 不把业务入参放进 `FlowConfig` / `WorkflowConfig`
- `vars` 仍仅用于运行中中间状态
