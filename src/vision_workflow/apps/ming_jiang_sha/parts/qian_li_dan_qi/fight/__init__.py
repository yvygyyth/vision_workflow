"""子流程：千里单骑战斗（选关后的开打 / 结算）。"""

from vision_workflow.apps.ming_jiang_sha.common.actions import confirm
from vision_workflow.apps.ming_jiang_sha.parts.qian_li_dan_qi.fight.actions import (
    click_auto,
    click_cancel,
    click_challenge_end,
    click_next_step,
    click_setting,
    log_reward_titles,
    move_aside,
)
from vision_workflow.module import Flow, Module, ModuleConfig, abort, onward, to
from vision_workflow.status import FULFILLED, REJECTED

_CLICK = {FULFILLED: onward, REJECTED: abort}
_OK = {FULFILLED: onward}

FLOW = Flow(
    id="fight",
    name="开打",
    description="确认进战 → 托管 → 等结束 → 下一步 / 确认",
    entry="confirm",
    modules=[
        Module(
            id="confirm",
            name="确认",
            description="公共确认框",
            event=confirm,
            on=_CLICK,
        ),
        Module(
            id="move_aside",
            name="移开鼠标",
            description="移到 (80,80)，避免挡住识图（勿用 0,0，会触发 FailSafe）",
            event=move_aside,
            on=_CLICK,
            config=ModuleConfig(delay_ms=1500),
        ),
        Module(
            id="click_cancel",
            name="取消",
            description="点取消；成功后等 1s",
            event=click_cancel,
            on=_CLICK,
            config=ModuleConfig(delay_ms=1000),
        ),
        Module(
            id="click_setting",
            name="点设置",
            description="识别并点击 setting；成功后等 500ms",
            event=click_setting,
            on=_CLICK,
            config=ModuleConfig(delay_ms=500),
        ),
        Module(
            id="click_auto",
            name="托管",
            description="点击自动战斗；找不到则回到点设置",
            event=click_auto,
            on={FULFILLED: onward, REJECTED: to("click_setting")},
        ),
        Module(
            id="click_challenge_end",
            name="挑战结束",
            description="最长约 10 分钟、每 5 秒轮询 challenge_end 并点击",
            event=click_challenge_end,
            on=_CLICK,
            config=ModuleConfig(delay_ms=1000),
        ),
        Module(
            id="next_step",
            name="下一步",
            description="点击「点击空白区域到下一步」",
            event=click_next_step,
            on=_CLICK,
        ),
        Module(
            id="settle_confirm",
            name="确认",
            description="结算确认；点完后进入赠礼三选一",
            event=click_next_step,
            on=_CLICK,
            config=ModuleConfig(delay_ms=1500),
        ),
        Module(
            id="log_reward_titles",
            name="识别赠礼标题",
            description="确认后 OCR 左/中/右三个赠礼标题区",
            event=log_reward_titles,
            on=_OK,
        ),
    ],
)
