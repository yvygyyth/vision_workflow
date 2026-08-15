"""common 图点击：跨流程复用的 UI（与 parts 专属 click 区分）。"""

from __future__ import annotations

from vision_workflow.events.builders.click import click
from vision_workflow.events.common.paths import COMMON_DIR
from vision_workflow.module import EventFn

click_max: EventFn = click().image(f"{COMMON_DIR}/max.png").execute()
click_ming_jiang_ce: EventFn = click().image(f"{COMMON_DIR}/ming_jiang_ce.png").execute()
click_ling_xi_box: EventFn = click().image(f"{COMMON_DIR}/ling_xi-box.png").execute()
