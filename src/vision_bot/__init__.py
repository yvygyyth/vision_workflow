"""vision_bot 包。"""

__version__ = "0.2.0"

from vision_bot.runtime.catalog import (
    DEFAULT_ROOT_ID,
    ROOT_FLOWS,
    get_root_flow,
    root_flow_choices,
    root_flow_ids,
)
from vision_bot.runtime.config import RunConfig
from vision_bot.runtime.runner import RunReport, run

__all__ = [
    "run",
    "RunConfig",
    "RunReport",
    "ROOT_FLOWS",
    "DEFAULT_ROOT_ID",
    "get_root_flow",
    "root_flow_choices",
    "root_flow_ids",
    "__version__",
]
