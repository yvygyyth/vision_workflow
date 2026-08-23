"""vision_bot 测试。"""

import threading
import time
from pathlib import Path

import pytest

from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.build import build_qian_li_dan_qi
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.detect import detect_hub, detect_qian_li
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.signals import build_registry
from vision_bot.core.models import MatchResult
from vision_bot.perception.snapshot import ScreenSnapshot
from vision_bot.runtime import RunContext, flow, mod, run_root
from vision_bot.runtime.registry import FlowRegistry
from vision_bot.runtime.result import Result
from vision_bot.jobs import JOBS, job_choices
from vision_bot.jobs import get_job, start


def test_registry_unique() -> None:
    reg = build_registry()
    assert len(reg.ids()) == len(set(reg.ids()))


def test_detect_qian_li_hub() -> None:
    snap = ScreenSnapshot(
        hits={
            "choice.challenge": MatchResult(found=True, image="x.png", center=(1, 2)),
        }
    )
    assert detect_qian_li(snap, None) == "qldq.battle_hub"  # type: ignore[arg-type]


def test_detect_hub_pick_battle() -> None:
    snap = ScreenSnapshot(
        hits={"choice.challenge": MatchResult(found=True, image="x.png")}
    )
    from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.detect import HUB_PICK_BATTLE

    assert detect_hub(snap, None) == HUB_PICK_BATTLE  # type: ignore[arg-type]


def test_flow_registry_build() -> None:
    root = build_qian_li_dan_qi()
    reg = FlowRegistry.build(root)
    assert reg.get("qldq") is root
    assert reg.get("qldq.fight").id == "qldq.fight"


def test_flow_registry_duplicate_id() -> None:
    child = mod("dup", "子", lambda ctx: Result.success())
    root = flow("root", "根", children=[child, mod("dup", "重复", lambda ctx: Result.success())])
    with pytest.raises(ValueError, match="重复"):
        FlowRegistry.build(root)


def test_sequential_modules() -> None:
    log: list[str] = []

    def a(ctx):
        log.append("a")
        return Result.success()

    def b(ctx):
        log.append("b")
        return Result.success()

    root = flow(
        "t",
        "测试",
        children=[
            mod("t.a", "A", a),
            mod("t.b", "B", b),
        ],
    )
    ctx = RunContext(base_dir=Path("."), registry=build_registry())
    report = run_root(root, ctx)
    assert report.success
    assert log == ["a", "b"]


def test_goto_jumps_to_target() -> None:
    log: list[str] = []

    def a(ctx):
        log.append("a")
        ctx.goto("t.c")
        return Result.success()

    def b(ctx):
        log.append("b")
        return Result.success()

    def c(ctx):
        log.append("c")
        return Result.success()

    root = flow(
        "t",
        "测试",
        children=[
            mod("t.a", "A", a),
            mod("t.b", "B", b),
            mod("t.c", "C", c),
        ],
    )
    ctx = RunContext(base_dir=Path("."), registry=build_registry())
    report = run_root(root, ctx)
    assert report.success
    assert log == ["a", "c"]


def test_relocate_on_entry() -> None:
    log: list[str] = []

    def a(ctx):
        log.append("a")
        return Result.success()

    def b(ctx):
        log.append("b")
        return Result.success()

    root = flow(
        "t",
        "测试",
        children=[
            mod("t.a", "A", a),
            mod("t.b", "B", b),
        ],
        relocate=[lambda ctx: "t.b"],
    )
    ctx = RunContext(base_dir=Path("."), registry=build_registry())
    report = run_root(root, ctx)
    assert report.success
    assert log == ["b"]


def test_jobs_registry() -> None:
    assert len(JOBS) == 3
    assert len(job_choices()) == len(JOBS)
    assert get_job("qian_li_dan_qi").name == "千里单骑"
    assert get_job("ba_wang_zhi_luan").name == "八王之乱"
    assert get_job("fee_day").name == "名将杀免费资源每日领取"
    with pytest.raises(KeyError):
        get_job("no_such_job")


def test_ba_wang_build() -> None:
    from vision_bot.apps.ming_jiang_sha.ba_wang_zhi_luan.build import build

    root = build()
    assert root.id == "ba_wang"
    reg = FlowRegistry.build(root)
    assert "ba_wang.battle_done" in reg.nodes


def test_fee_day_build() -> None:
    from vision_bot.apps.ming_jiang_sha.fee_day.build import build_fee_day

    root = build_fee_day()
    assert root.id == "fee_day"
    assert len(root.children) == 7
    reg = FlowRegistry.build(root)
    assert "fee_day.mail.open" in reg.nodes


def test_start_unknown_job() -> None:
    with pytest.raises(KeyError):
        start("no_such_job")


def test_cancel_during_wait() -> None:
    from vision_bot.actions.context import ActionContext
    from vision_bot.actions.wait import wait_image
    from vision_bot.runtime.cancel import CancelledError

    cancel = threading.Event()
    ctx = ActionContext(base_dir=Path("."), cancelled=cancel.is_set)

    def _set_cancel() -> None:
        time.sleep(0.15)
        cancel.set()

    threading.Thread(target=_set_cancel, daemon=True).start()
    with pytest.raises(CancelledError):
        wait_image(
            ctx,
            ("data/ming_jiang_sha/mail/email.png",),
            threshold=0.8,
            timeout=30.0,
            interval=0.1,
            region=None,
            grayscale=None,
        )
