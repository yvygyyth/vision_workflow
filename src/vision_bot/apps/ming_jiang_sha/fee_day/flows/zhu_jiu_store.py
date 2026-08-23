"""煮酒店铺。"""

from __future__ import annotations

from vision_bot.apps.ming_jiang_sha.actions import (
    step_click_ling_xi_box,
    step_click_ming_jiang_ce,
    step_click_max,
    step_confirm,
    step_go_back,
    step_space_close,
)
from vision_bot.apps.ming_jiang_sha.flow_helpers import do_click
from vision_bot.apps.ming_jiang_sha.paths import DATA_ROOT
from vision_bot.runtime.builders import flow, mod
from vision_bot.runtime.flow import Flow
from vision_bot.runtime.result import Result

_DIR = f"{DATA_ROOT}/zhu_jiu_store"


def _finish(ctx) -> Result:
    step_go_back(ctx)
    return Result.success()


def build() -> Flow:
    return flow(
        "fee_day.zhu_jiu_store",
        "煮酒店铺",
        children=[
            mod("fee_day.zhu_jiu_store.entry", "打开入口", lambda ctx: do_click(ctx, f"{_DIR}/entry.png")),
            mod("fee_day.zhu_jiu_store.qing_mei_store", "青梅店", lambda ctx: do_click(ctx, f"{_DIR}/qing_mei-store.png")),
            mod("fee_day.zhu_jiu_store.ming_jiang_ce", "名将册", step_click_ming_jiang_ce),
            mod("fee_day.zhu_jiu_store.buy", "购买", step_confirm),
            mod("fee_day.zhu_jiu_store.space_close", "关闭弹窗", step_space_close),
            mod("fee_day.zhu_jiu_store.ling_xi_box", "灵犀盒", step_click_ling_xi_box),
            mod("fee_day.zhu_jiu_store.max", "最大", step_click_max),
            mod("fee_day.zhu_jiu_store.buy2", "购买2", step_confirm),
            mod("fee_day.zhu_jiu_store.space_close2", "关闭弹窗2", step_space_close),
            mod("fee_day.zhu_jiu_store.close", "关闭", step_go_back),
            mod("fee_day.zhu_jiu_store.return_btn", "返回", _finish),
        ],
    )
