from config.actions import (
    action_click_email,
    action_handle_fail,
    action_log_done,
    judge_email_still_there,
)
from vision_workflow.module import END, FAIL, Module

# 平级模块：每个都有 id，生命周期结束后跳到任意模块
MODULES = [
    Module(
        id="click_email",
        action=action_click_email,          # 本模块要做的事（可不识图）
        judge=judge_email_still_there,      # 判定函数（可省略）
        success="done",                     # 成功 → 跳到 done
        fail="handle_fail",                 # 失败 → 跳到 handle_fail（也可写回 click_email 做循环）
        max_loops=3,
    ),
    Module(
        id="done",
        action=action_log_done,
        success=END,
        fail=END,
    ),
    Module(
        id="handle_fail",
        action=action_handle_fail,
        success=END,
        fail=FAIL,
    ),
]

ENTRY = "click_email"  # 从哪个模块开始；也可运行时指定任意 id
