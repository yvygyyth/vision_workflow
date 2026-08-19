"""八王之乱：单个 Flow 覆盖准备 → 选将 → 战斗 → 循环。"""

from vision_workflow.apps.ming_jiang_sha.parts.ba_wang_zhi_luan.actions import (
    ENTER_BATTLE,
    battle_round_done,
    click_auto,
    click_challenge_end,
    click_next_step_if_any,
    click_ready,
    click_ok_if_any,
    confirm_ready,
    detect_role,
    move_aside,
    pick_all_sixes,
    poll_click_start,
    wait_click_setting,
    wait_game_start,
)
from vision_workflow.module import Flow, Module, back, onward, to
from vision_workflow.status import FULFILLED, REJECTED

_CLICK = {FULFILLED: onward, REJECTED: back}
_TO_WAIT = {FULFILLED: to("wait_game_start"), REJECTED: back}
_TO_FIGHT = {FULFILLED: to("move_aside"), REJECTED: back}
_TO_READY = {FULFILLED: to("detect_role"), REJECTED: back}

FLOW = Flow(
    id="ba_wang_zhi_luan",
    name="八王之乱",
    description="房间准备 → 选将点6 → 无赠礼战斗 → 回准备循环",
    entry="detect_role",
    modules=[
        Module(
            id="detect_role",
            name="判定身份",
            description="识别准备/取消准备→房员，否则→房主",
            event=detect_role,
            on={
                "member": to("click_ready"),
                "member_ready": to("wait_game_start"),
                "owner": to("poll_start"),
                REJECTED: back,
            },
        ),
        Module(
            id="click_ready",
            name="点击准备",
            description="识别 zhun_bei 并点击",
            event=click_ready,
            on=_CLICK,
        ),
        Module(
            id="confirm_ready",
            name="确认已准备",
            description="核验是否变为 un_zhun+bei",
            event=confirm_ready,
            on={
                FULFILLED: to("wait_game_start"),
                "still_ready": to("click_ready"),
                REJECTED: back,
            },
        ),
        Module(
            id="poll_start",
            name="轮询开始",
            description="最长约 10 分钟、每 1.5 秒轮询 start 并点击",
            event=poll_click_start,
            on=_TO_WAIT,
        ),
        Module(
            id="wait_game_start",
            name="等待开局",
            description="等 6 或 setting 出现；已在战斗则跳过选将",
            event=wait_game_start,
            on={
                FULFILLED: to("pick_six"),
                ENTER_BATTLE: to("move_aside"),
                REJECTED: back,
            },
        ),
        Module(
            id="pick_six",
            name="选将点6",
            description="扫描一次，依次点场上所有 6",
            event=pick_all_sixes,
            on={FULFILLED: to("click_ok"), REJECTED: back},
        ),
        Module(
            id="click_ok",
            name="点确定",
            description="识别 ok 有则点，无则跳过",
            event=click_ok_if_any,
            on=_TO_FIGHT,
        ),
        Module(
            id="move_aside",
            name="移开鼠标",
            description="移到 (80,80)，避免挡住识图",
            event=move_aside,
            on=_CLICK,
        ),
        Module(
            id="wait_setting",
            name="等 setting 并点击",
            description="轮询 setting，出现即点击（战斗开始）",
            event=wait_click_setting,
            on={FULFILLED: onward, REJECTED: back},
        ),
        Module(
            id="click_auto",
            name="托管",
            description="点击自动战斗；找不到则回到等 setting",
            event=click_auto,
            on={FULFILLED: onward, REJECTED: back},
        ),
        Module(
            id="click_challenge_end",
            name="挑战结束",
            description="最长约 10 分钟、每 5 秒轮询 challenge_end 并点击",
            event=click_challenge_end,
            on=_CLICK,
        ),
        Module(
            id="next_step",
            name="下一步",
            description="有下一步就点；没有也继续",
            event=click_next_step_if_any,
            on={FULFILLED: to("battle_done"), REJECTED: back},
        ),
        Module(
            id="battle_done",
            name="本局结束",
            description="回到房间准备模块",
            event=battle_round_done,
            on=_TO_READY,
        ),
    ],
)
