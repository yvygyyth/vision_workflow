# 店长特供（dian_zhang_te_gong）流程设计

## 目标

为异环「店长特供」增加可选根流程：点「开始营业」后连点固定坐标，直到出现「领取」并点击后结束。

## 流程

1. 识别并点击 `data/yi_huan/dian_zhang_te_gong/start.png`
2. 循环：每 0.2s 点击绝对坐标 `(120, 600)`；每 2s 探测一次 `ling_qv.png`
3. 探测到后点击「领取」，流程成功结束

无 relocate、无总超时。

## 结构

- 新包 `apps/yi_huan/`（paths / registry）
- `apps/yi_huan/dian_zhang_te_gong/{build,steps}.py`（仿八王之乱）
- `runtime/catalog.py` 合并异环根流程注册

## 非目标

不领取后的后续 UI、不挂工具 Flow、不写入名将杀包。
