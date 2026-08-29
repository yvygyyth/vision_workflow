"""妃妃 mod。"""

from __future__ import annotations

from vision_bot.apps.ming_jiang_sha.paths import QLDQ
from vision_bot.events import click_match
from vision_bot.runtime.result import Result
from vision_bot.vision import find

_OPTS = (
    f"{QLDQ}/fei_fei/i_help_you.png",
    f"{QLDQ}/fei_fei/sleep.png",
    f"{QLDQ}/fei_fei/bargaining.png",
)


def choose(ctx) -> Result:
    for path in _OPTS:
        result = find(path, timeout=0.8)
        if result.ok:
            return click_match(result.value)
    return Result.fail("妃妃选项未识别")
