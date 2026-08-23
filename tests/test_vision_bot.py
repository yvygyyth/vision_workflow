"""vision_bot 测试。"""

import pytest

from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.build import build_qian_li_dan_qi
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.detect import detect_hub, detect_qian_li
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.signals import build_registry, snap_found
from vision_bot.core.models import MatchResult
from vision_bot.perception.snapshot import ScreenSnapshot
from vision_bot.runtime import Flow
from vision_bot.runtime.flow import StepResult
from vision_bot.runtime.types import BACK_TO_HUB, END, ENTER_BATTLE, FAIL, FIGHT
from vision_bot.jobs import JOBS, job_choices
from vision_bot.start import get_job, start


def test_registry_unique() -> None:
    reg = build_registry()
    assert len(reg.ids()) == len(set(reg.ids()))


def test_detect_qian_li_hub() -> None:
    snap = ScreenSnapshot(
        hits={
            "choice.challenge": MatchResult(found=True, image="x.png", center=(1, 2)),
        }
    )
    assert detect_qian_li(snap, None) == "battle_hub"  # type: ignore[arg-type]


def test_detect_hub_pick_battle() -> None:
    snap = ScreenSnapshot(
        hits={"choice.challenge": MatchResult(found=True, image="x.png")}
    )
    from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.detect import HUB_PICK_BATTLE

    assert detect_hub(snap, None) == HUB_PICK_BATTLE  # type: ignore[arg-type]


def test_step_result_end() -> None:
    r = StepResult.end(FIGHT)
    assert r.next_id is END
    assert r.outcome == FIGHT


def test_normalize_steps_from_callable() -> None:
    def step(ctx):
        return StepResult.ok()

    flow = Flow(
        id="t",
        entry="a",
        steps={"a": step},
    )
    assert callable(flow.steps["a"])
    assert flow.steps["a"] is step


def test_routes_and_build_root() -> None:
    def step(ctx):
        return StepResult.ok()

    flow = Flow(
        id="t",
        entry="a",
        steps={"a": step, "b": step},
        routes={"a": {FAIL: "b"}},
    )
    assert flow.routes["a"][FAIL] == "b"

    root = build_qian_li_dan_qi()
    assert root.entry == "enter_battle"
    assert "battle_hub" in root.steps
    assert isinstance(root.steps["fight"], Flow)
    assert root.on[BACK_TO_HUB] == "battle_hub"
    assert root.on[FIGHT] == "fight"
    assert root.on[ENTER_BATTLE] == "enter_battle"


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

    flow = build()
    assert flow.id == "ba_wang_zhi_luan"
    assert flow.entry == "detect_role"
    assert "battle_done" in flow.steps


def test_fee_day_build() -> None:
    from vision_bot.apps.ming_jiang_sha.fee_day.build import build_fee_day

    flow = build_fee_day()
    assert flow.id == "fee_day"
    assert flow.entry == "mail"
    assert "gong_hui" in flow.steps
    assert flow.on["mail_done"] == "dang_qing_ge"


def test_start_unknown_job() -> None:
    with pytest.raises(KeyError):
        start("no_such_job")


def test_cancel_during_wait() -> None:
    import threading
    import time
    from pathlib import Path

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
