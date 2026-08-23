"""可启动任务注册表。"""

from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from vision_bot.runtime.runner import RunReport

RunFn = Callable[..., RunReport]


@dataclass(frozen=True)
class Job:
    id: str
    name: str
    run: RunFn


def _run_qian_li_dan_qi(
    *,
    base_dir: Path | None = None,
    cancel_event: threading.Event | None = None,
    wu_jiang: str = "吕布",
) -> RunReport:
    from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.run import run

    return run(base_dir=base_dir, cancel_event=cancel_event, wu_jiang=wu_jiang)


def _run_ba_wang_zhi_luan(
    *,
    base_dir: Path | None = None,
    cancel_event: threading.Event | None = None,
    **_: object,
) -> RunReport:
    from vision_bot.apps.ming_jiang_sha.ba_wang_zhi_luan.run import run

    return run(base_dir=base_dir, cancel_event=cancel_event)


def _run_fee_day(
    *,
    base_dir: Path | None = None,
    cancel_event: threading.Event | None = None,
    **_: object,
) -> RunReport:
    from vision_bot.apps.ming_jiang_sha.fee_day.run import run

    return run(base_dir=base_dir, cancel_event=cancel_event)


# 新增任务：在此追加一项即可，UI 下拉会自动出现
JOBS: list[Job] = [
    Job(id="qian_li_dan_qi", name="千里单骑", run=_run_qian_li_dan_qi),
    Job(id="ba_wang_zhi_luan", name="八王之乱", run=_run_ba_wang_zhi_luan),
    Job(id="fee_day", name="名将杀免费资源每日领取", run=_run_fee_day),
]

DEFAULT_JOB_ID = JOBS[0].id if JOBS else ""


def get_job(job_id: str) -> Job:
    for job in JOBS:
        if job.id == job_id:
            return job
    raise KeyError(f"未知任务: {job_id}，可选: {[j.id for j in JOBS]}")


def job_choices() -> list[tuple[str, str]]:
    """UI 下拉：(显示名, job_id)。"""
    return [(job.name, job.id) for job in JOBS]


def start(
    job_id: str,
    *,
    base_dir: Path | None = None,
    cancel_event: threading.Event | None = None,
    **kwargs: object,
) -> RunReport:
    """按 id 启动注册表中的任务。"""
    job = get_job(job_id)
    return job.run(base_dir=base_dir, cancel_event=cancel_event, **kwargs)
