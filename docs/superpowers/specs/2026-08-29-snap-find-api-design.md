# 识图 API 统一：双原语 + timeout 区分快慢

日期：2026-08-29  
状态：已实现（不向后兼容）

## 架构

```text
core.vision
  find_image   — 单模板原语（自带 timeout/interval）
  find_images  — 多模板同帧原语（每轮一帧；timeout>0 时轮询至任一命中）
  find_all_images — 同一模板多目标
       ↑
vision
  find(...)    — 默认会话 timeout（慢查）
  snap(...)    — timeout=0（快查）
  find_all(...)
```

业务只从 `vision_bot.vision` 导入。已删除：`find_image_with_options`、`perception.snapshot`（`match` / `capture_screen` / `resolve_template` / re-export）。

## 返回

| 入参 | 返回 |
|------|------|
| 单图 | `Result` |
| 多图 | `ScreenSnapshot`（`path → Result`） |
