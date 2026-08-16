"""子流程：霸青商店。"""

from vision_workflow.apps.ming_jiang_sha.common.actions import buy, click_max, go_back, space_close
from vision_workflow.apps.ming_jiang_sha.parts.ba_qing_store.actions import (
    click_copper_tab,
    click_entry_icon,
    click_free_bingli,
    click_gold_tab,
    click_jinlan_tab,
    click_lingxi_box,
    click_ming_jiang_ce,
    scroll_down,
)
from vision_workflow.module import Flow, Module, abort, onward
from vision_workflow.status import FULFILLED, REJECTED

_CLICK = {FULFILLED: onward, REJECTED: abort}
_OK = {FULFILLED: onward}

FLOW = Flow(
    id="ba_qing_store",
    name="霸青商店",
    description="领取霸青商店免费兵力、灵犀宝匣与名将册",
    entry="entry_icon",
    modules=[
        Module(id="entry_icon", name="打开霸青商店", description="点击入口图标", event=click_entry_icon, on=_CLICK),
        Module(id="gold_tab", name="金币页签", description="切换到金币页签", event=click_gold_tab, on=_CLICK),
        Module(id="free_bingli", name="免费兵力", description="选中免费兵力", event=click_free_bingli, on=_CLICK),
        Module(id="buy_0", name="0 购买", description="点击 0 购买", event=buy, on=_CLICK),
        Module(id="space_close", name="关闭弹窗", description="Esc 关闭购买结果弹窗", event=space_close(), on=_OK),
        Module(id="copper_tab", name="铜币页签", description="切换到铜币页签", event=click_copper_tab, on=_CLICK),
        Module(id="lingxi_box", name="灵犀宝匣", description="选中灵犀宝匣", event=click_lingxi_box, on=_CLICK),
        Module(id="max", name="数量最大", description="将购买数量拉满", event=click_max, on=_CLICK),
        Module(id="buy_500", name="500 购买", description="点击 500 购买", event=buy, on=_CLICK),
        Module(id="space_close2", name="关闭弹窗", description="Esc 关闭购买结果弹窗", event=space_close(), on=_OK),
        Module(id="space_close3", name="关闭弹窗", description="Esc 再关一次", event=space_close(), on=_OK),
        Module(id="jinlan_tab", name="锦囊页签", description="切换到锦囊页签", event=click_jinlan_tab, on=_CLICK),
        Module(id="scroll", name="下滑列表", description="向下滚动列表", event=scroll_down, on=_OK),
        Module(id="ming_jiang_ce", name="名将册", description="选中名将册", event=click_ming_jiang_ce, on=_CLICK),
        Module(id="buy_200", name="200 购买", description="点击 200 购买", event=buy, on=_CLICK),
        Module(id="space_close4", name="关闭弹窗", description="Esc 关闭购买结果弹窗", event=space_close(), on=_OK),
        Module(id="go_back", name="返回", description="Esc 返回主界面", event=go_back(), on=_OK),
    ],
)
