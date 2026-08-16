"""千里单骑 · 开打动作。"""

from __future__ import annotations

from vision_workflow.apps.ming_jiang_sha.common.paths import DATA_ROOT
from vision_workflow.events import click, do, move
from vision_workflow.module import EventFn, ModuleContext
from vision_workflow.status import FULFILLED, OutcomeKey
from vision_workflow.vision import grab_region, image_to_text

_DIR = f"{DATA_ROOT}/qian_li_dan_qi/fight"

# 结算三选一标题区（相对模板基准；grab_region 会 fit）
REWARD_TITLE_REGIONS: tuple[tuple[int, int, int, int], ...] = (
    (360, 1050, 290, 50),
    (1140, 1050, 290, 50),
    (1910, 1050, 290, 50),
)

click_cancel: EventFn = do(move().image(f"{_DIR}/cancel.png"), click())
# 勿用 (0,0)：PyAutoGUI 角落 FailSafe 会导致后续操作抛异常
move_aside: EventFn = do(move().to(80, 80).raw())
click_setting: EventFn = do(move().image(f"{_DIR}/setting.png"), click())
click_auto: EventFn = do(move().image(f"{_DIR}/auto.png"), click())
click_challenge_end: EventFn = do(
    move().image(f"{_DIR}/challenge_end.png").match(timeout=600, interval=5),
    click(),
)
click_next_step: EventFn = do(move().image(f"{_DIR}/next_step.png"), click())


def log_reward_titles(m: ModuleContext) -> OutcomeKey:
    """OCR 三个赠礼标题，按优先表选出要点的槽（暂不点击；信物在下一步）。"""
    from datetime import datetime
    from pathlib import Path

    from vision_workflow.apps.ming_jiang_sha.parts.qian_li_dan_qi.utils import (
        get_battle_state,
        parse_general_name,
        pick_reward_slot,
    )

    out_dir = Path("logs/reward_ocr") / datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir.mkdir(parents=True, exist_ok=True)

    titles: list[str] = []
    lines: list[str] = []
    for i, region in enumerate(REWARD_TITLE_REGIONS, start=1):
        img = grab_region(region)
        path = out_dir / f"slot_{i}.png"
        img.save(path)
        text = image_to_text(img)
        titles.append(text)
        shown = text if text else "(空)"
        lines.append(f"{i}:{shown}")
        m.log("【赠礼OCR】槽位%s %s → %s 已保存 %s", i, region, shown, path)

    state = get_battle_state(m.ctx)
    slot = pick_reward_slot(titles, state)
    picked = parse_general_name(titles[slot]) or f"槽{slot + 1}"
    m.log("【赠礼选择】选槽位%s → %s", slot + 1, picked)
    m.reason = f"{'；'.join(lines)} → 选{slot + 1}:{picked} | 截图 {out_dir.resolve()}"
    m.value = {"titles": titles, "slot": slot, "name": picked}
    return FULFILLED
