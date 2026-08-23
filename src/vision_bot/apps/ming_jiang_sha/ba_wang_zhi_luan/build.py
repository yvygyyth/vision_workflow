"""组装八王之乱 Flow。"""

from __future__ import annotations

from vision_bot.apps.ming_jiang_sha.ba_wang_zhi_luan import steps as s
from vision_bot.runtime.flow import Flow
from vision_bot.runtime.types import FAIL, OK


def build() -> Flow:
    return Flow(
        id="ba_wang_zhi_luan",
        name="八王之乱",
        entry="detect_role",
        steps={
            "detect_role": s.detect_role,
            "click_ready": s.click_ready,
            "confirm_ready": s.confirm_ready,
            "poll_start": s.poll_click_start,
            "wait_game_start": s.wait_game_start,
            "pick_six": s.pick_all_sixes,
            "click_ok": s.click_ok_if_any,
            "move_aside": s.move_aside,
            "wait_setting": s.wait_click_setting,
            "click_auto": s.click_auto,
            "click_challenge_end": s.click_challenge_end,
            "next_step": s.click_next_step_if_any,
            "battle_done": s.battle_round_done,
        },
        routes={
            "detect_role": {
                "member": "click_ready",
                "member_ready": "wait_game_start",
                "owner": "poll_start",
            },
            "click_ready": {OK: "confirm_ready"},
            "confirm_ready": {
                OK: "wait_game_start",
                "still_ready": "click_ready",
            },
            "poll_start": {OK: "wait_game_start"},
            "wait_game_start": {
                OK: "pick_six",
                s.IN_BATTLE: "move_aside",
            },
            "pick_six": {OK: "click_ok"},
            "click_ok": {OK: "move_aside"},
            "move_aside": {OK: "wait_setting"},
            "wait_setting": {OK: "click_auto"},
            "click_auto": {FAIL: "wait_setting"},
            "click_challenge_end": {OK: "next_step"},
            "next_step": {OK: "battle_done"},
        },
    )
