"""公会店铺。"""

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

_DIR = f"{DATA_ROOT}/gong_hui"


def _finish(ctx) -> Result:
    step_go_back(ctx)
    return Result.success()


def build() -> Flow:
    return flow(
        "fee_day.gong_hui",
        "公会店铺",
        children=[
            mod(
                "fee_day.gong_hui.entry",
                "打开公会",
                lambda ctx: do_click(
                    ctx,
                    f"{_DIR}/gong-hui-ru-kou.png",
                    f"{_DIR}/gong-hui-ru-kou-2.png",
                    timeout=5.0,
                ),
            ),
            mod("fee_day.gong_hui.open_store", "打开店铺", lambda ctx: do_click(ctx, f"{_DIR}/gong-hui-store.png")),
            mod("fee_day.gong_hui.ming_jiang_ce", "名将册", step_click_ming_jiang_ce),
            mod("fee_day.gong_hui.max", "最大", step_click_max),
            mod("fee_day.gong_hui.buy", "购买", step_confirm),
            mod("fee_day.gong_hui.space_close", "关闭弹窗", step_space_close),
            mod("fee_day.gong_hui.ling_xi_box", "灵犀盒", step_click_ling_xi_box),
            mod("fee_day.gong_hui.max2", "最大2", step_click_max),
            mod("fee_day.gong_hui.buy2", "购买2", step_confirm),
            mod("fee_day.gong_hui.space_close2", "关闭弹窗2", step_space_close),
            mod("fee_day.gong_hui.wen_ding_ling", "文定令", lambda ctx: do_click(ctx, f"{_DIR}/wen_ding_ling.png")),
            mod("fee_day.gong_hui.max3", "最大3", step_click_max),
            mod("fee_day.gong_hui.buy3", "购买3", step_confirm),
            mod("fee_day.gong_hui.space_close3", "关闭弹窗3", step_space_close),
            mod("fee_day.gong_hui.tian_ming_ling", "天命令", lambda ctx: do_click(ctx, f"{_DIR}/tian_ming_ling.png")),
            mod("fee_day.gong_hui.max4", "最大4", step_click_max),
            mod("fee_day.gong_hui.buy4", "购买4", step_confirm),
            mod("fee_day.gong_hui.space_close4", "关闭弹窗4", step_space_close),
            mod("fee_day.gong_hui.tian_fa_ling", "天法令", lambda ctx: do_click(ctx, f"{_DIR}/tian_fa_ling.png")),
            mod("fee_day.gong_hui.max5", "最大5", step_click_max),
            mod("fee_day.gong_hui.buy5", "购买5", step_confirm),
            mod("fee_day.gong_hui.space_close5", "关闭弹窗5", step_space_close),
            mod("fee_day.gong_hui.jun_ling_zhuang", "军令状", lambda ctx: do_click(ctx, f"{_DIR}/jun_ling_zhuang.png")),
            mod("fee_day.gong_hui.max6", "最大6", step_click_max),
            mod("fee_day.gong_hui.buy6", "购买6", step_confirm),
            mod("fee_day.gong_hui.space_close6", "关闭弹窗6", step_space_close),
            mod("fee_day.gong_hui.close", "关闭", step_go_back),
            mod("fee_day.gong_hui.return_btn", "返回", _finish),
        ],
    )
