"""千里单骑流程动作。"""

from vision_workflow.apps.ming_jiang_sha.common.paths import DATA_ROOT
from vision_workflow.events import click, do, input_text, move
from vision_workflow.module import EventFn, ModuleContext
from vision_workflow.status import OutcomeKey

_DIR = f"{DATA_ROOT}/qian_li_dan_qi"

click_select_wu_jiang: EventFn = do(
    move().image(f"{_DIR}/select_wu_jiang.png"), click()
)
# 识 search 后向左偏 50px 再点（打开搜索输入）
click_search_input: EventFn = do(
    move().image(f"{_DIR}/search.png"),
    move().by(-50, 0),
    click(),
)


def type_wu_jiang(m: ModuleContext) -> OutcomeKey:
    """输入武将名（来自 Flow 入参 wu_jiang，默认吕布）。"""
    name = str(m.params.get("wu_jiang", "吕布"))
    return input_text(name).execute()(m)
