"""子流程：活动。"""

from vision_workflow.apps.ming_jiang_sha.common.actions import go_back, space_close
from vision_workflow.apps.ming_jiang_sha.parts.actaivity.actions import (
    click_huo_dong,
    click_yue_ling,
    click_gua_xiang,
    click_ling_qv,
    scroll_down,
    move_aside,
)
from vision_workflow.module import Flow, Module, abort, onward
from vision_workflow.status import FULFILLED, REJECTED

_CLICK = {FULFILLED: onward, REJECTED: abort}
_OK = {FULFILLED: onward}

FLOW = Flow(
    id="activity",
    name="活动",
    description="领取活动奖励",
    entry="entry_icon",
    modules=[
        Module(id="entry_icon", name="打开活动", description="点击入口图标", event=click_huo_dong, on=_CLICK),
        Module(id="bu_gua", name="移动鼠标至卜卦牌", description="移到 (1400,600)点击", event=move_aside, on=_CLICK,config={"delay_ms": 1000}),
        Module(id="bu_gua2", name="再次点击卜卦牌", description="再次点击", event=move_aside,  on=_CLICK),
        Module(id="space_close", name="关闭弹窗", description="Esc 关闭购买结果弹窗", event=space_close(), on=_OK),
        Module(id="gua_xiang", name="点击列表", description="点击列表", event=click_gua_xiang, on=_CLICK),
        Module(id="scroll", name="下滑列表", description="向下滚动列表", event=scroll_down, on=_OK),
        Module(id="yue_ling", name="军需月令", description="点击军需月令", event=click_yue_ling, on=_CLICK),
        Module(id="sui_yin", name="领取碎银", description="点击领取", event=click_ling_qv, on=_CLICK),
        Module(id="go_back", name="返回", description="Esc 返回主界面", event=go_back(), on=_OK),
    ],
)