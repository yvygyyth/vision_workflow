"""子流程：日常送花（骨架，按需补全）。"""

from vision_workflow.apps.ming_jiang_sha.parts.song_hua.actions import (
    click_entry,
    focus_search_input,
    type_Friend,
)
from vision_workflow.module import Flow, Module, abort, onward
from vision_workflow.status import FULFILLED, REJECTED

_CLICK = {FULFILLED: onward, REJECTED: abort}

FLOW = Flow(
    id="song_hua",
    name="日常送花",
    description="好友搜索与送花（待补全）",
    entry="entry",
    modules=[
        Module(
            id="entry",
            name="进入好友",
            description="点击好友入口",
            event=click_entry,
            on=_CLICK,
        ),
        Module(
            id="search",
            name="搜索栏",
            description="点击搜索栏",
            event=focus_search_input,
            on=_CLICK,
        ),
        Module(
            id="type_friend",
            name="输入好友",
            description="粘贴好友名",
            event=type_Friend,
            on=_CLICK,
        ),
    ],
)
