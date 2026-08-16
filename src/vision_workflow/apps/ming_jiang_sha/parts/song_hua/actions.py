"""好友送花流程动作。"""

from vision_workflow.apps.ming_jiang_sha.common.paths import DATA_ROOT
from vision_workflow.events import click, do, move
from vision_workflow.module import EventFn
from vision_workflow.module import EventFn, ModuleContext

_DIR = f"{DATA_ROOT}/song_hua"

click_entry: EventFn = do(
    move().image(f"{_DIR}/hao_you.png"),
    click(),
)
click_gong_hui_store: EventFn = do(move().image(f"{_DIR}/gong-hui-store.png"), click())
click_wen_ding_ling: EventFn = do(move().image(f"{_DIR}/wen_ding_ling.png"), click())
click_tian_ming_ling: EventFn = do(move().image(f"{_DIR}/tian_ming_ling.png"), click())
click_tian_fa_ling: EventFn = do(move().image(f"{_DIR}/tian_fa_ling.png"), click())
click_jun_ling_zhuang: EventFn = do(move().image(f"{_DIR}/jun_ling_zhuang.png"), click())

focus_search_input: EventFn = do(
    move().image(f"{_DIR}/sou_suo.png"),
    click().pause(0.3),
)

def type_Friend(m: ModuleContext) -> OutcomeKey:
    """写入好友名（入参 friend_name）。"""
    name = str(m.params.get("friend_name", "张飞")).strip()
    if not name:
        m.reason = "入参 friend_name 为空"
        return REJECTED
    m.log("type_Friend %s", name)
    m.sleep(0.2)
    return input_text(name).paste().pause(0.2).execute()(m)