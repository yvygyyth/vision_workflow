"""组装八王之乱 Flow。"""

from __future__ import annotations

from vision_bot.apps.ming_jiang_sha.ba_wang_zhi_luan import steps as s
from vision_bot.runtime.builders import flow, mod
from vision_bot.runtime.flow import Flow


def build() -> Flow:
    return flow(
        "ba_wang",
        "八王之乱",
        children=[
            mod("ba_wang.click_ready", "点击准备", s.click_ready),
            mod("ba_wang.confirm_ready", "确认准备", s.confirm_ready),
            mod("ba_wang.poll_start", "等待开始", s.poll_click_start),
            mod("ba_wang.wait_game_start", "等待开局", s.wait_game_start),
            mod("ba_wang.pick_six", "选六点", s.pick_all_sixes),
            mod("ba_wang.click_ok", "点确定", s.click_ok_if_any),
            mod("ba_wang.move_aside", "移开鼠标", s.move_aside),
            mod("ba_wang.wait_setting", "点设置", s.wait_click_setting),
            mod("ba_wang.click_auto", "点自动", s.click_auto),
            mod("ba_wang.click_challenge_end", "等挑战结束", s.click_challenge_end),
            mod("ba_wang.next_step", "下一步", s.click_next_step_if_any),
            mod("ba_wang.battle_done", "回合结束", s.battle_round_done),
        ],
        relocate=s.relocate_role,
    )
