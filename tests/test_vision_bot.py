"""vision_bot 测试。"""

import threading
import time
from pathlib import Path

import pytest

from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.build import build_qian_li_dan_qi
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.flows.battle_hub import HUB_PICK_BATTLE, detect as detect_hub
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.flows.qian_li import detect as detect_qian_li
from vision_bot.core.models import MatchResult
from vision_bot.perception.snapshot import ScreenSnapshot
from vision_bot.runtime import flow, mod, run
from vision_bot.runtime.catalog import ROOT_FLOWS, get_root_flow, registry_for, root_flow_choices
from vision_bot.runtime.config import RunConfig
from vision_bot.runtime.registry import FlowRegistry
from vision_bot.runtime.result import Result


def test_qldq_registry() -> None:
    reg = registry_for("qldq")
    assert "enter.start" in reg.ids()
    assert "choice.challenge" in reg.ids()


def test_detect_qian_li_hub() -> None:
    snap = ScreenSnapshot(
        hits={
            "choice.challenge": MatchResult(found=True, image="x.png", center=(1, 2)),
        }
    )
    assert detect_qian_li(snap) == "qldq.battle_hub"


def test_detect_hub_pick_battle() -> None:
    snap = ScreenSnapshot(
        hits={"choice.challenge": MatchResult(found=True, image="x.png")}
    )
    assert detect_hub(snap, None) == HUB_PICK_BATTLE  # type: ignore[arg-type]


def test_flow_registry_build() -> None:
    root = build_qian_li_dan_qi()
    reg = FlowRegistry.build(root)
    assert reg.get("qldq") is root
    assert reg.get("qldq.fight").id == "qldq.fight"
    assert reg.get("qldq.ba_qing_store.choose_token").id == "qldq.ba_qing_store.choose_token"
    assert reg.get("qldq.fight.choose_reward_kind").id == "qldq.fight.choose_reward_kind"


def test_pick_reward_slot_priority() -> None:
    from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.state import BattleState
    from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.utils.rewards import RewardKind, pick_reward_slot

    state = BattleState()
    titles = ["甘宁赠礼", "刘表赠礼", "未知赠礼"]
    assert pick_reward_slot(titles, state) == 0

    state.mark_general_reward("甘宁", RewardKind.TOKEN)
    state.mark_general_reward("甘宁", RewardKind.BUFF)
    assert pick_reward_slot(titles, state) == 1


def test_pick_token_slot() -> None:
    from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.flows.ba_qing_store import pick_token_slot

    titles = ["(空)", "熏炉 x1", "铃铛"]
    assert pick_token_slot(titles) == 1
    assert pick_token_slot(["普通物品", "普通物品2", "普通物品3"]) is None


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
    report = run(root, RunConfig(), base_dir=Path("."))
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
    report = run(root, RunConfig(), base_dir=Path("."))
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
    report = run(root, RunConfig(), base_dir=Path("."))
    assert report.success
    assert log == ["b"]


def test_root_flow_catalog() -> None:
    assert len(ROOT_FLOWS) == 3
    assert len(root_flow_choices()) == 3
    assert get_root_flow("qldq").name == "千里单骑"
    assert get_root_flow("ba_wang").name == "八王之乱"
    assert get_root_flow("fee_day").name == "名将杀免费资源每日领取"
    with pytest.raises(KeyError):
        get_root_flow("no_such")


def test_run_from_entry() -> None:
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
    report = run(root, RunConfig(entry_id="t.b"))
    assert report.success
    assert log == ["b"]


def test_params_scope() -> None:
    seen: list[str] = []

    def child_mod(ctx):
        seen.append(ctx.params.get("k", ""))
        return Result.success()

    def root_mod(ctx):
        seen.append(f"root:{ctx.params.get('k', '')}")
        return Result.success()

    inner = flow("t.inner", "内", params={"k": "inner"}, children=[mod("t.inner.m", "M", child_mod)])
    root = flow(
        "t",
        "测试",
        params={"k": "root"},
        children=[
            mod("t.r", "R", root_mod),
            inner,
        ],
    )
    run(root, RunConfig())
    assert seen == ["root:root", "root"]


def test_params_override_on_entry_flow() -> None:
    got: list[str] = []

    def m(ctx):
        got.append(ctx.params.get("x", ""))
        return Result.success()

    inner = flow("t.inner", "内", params={"x": "default"}, children=[mod("t.inner.m", "M", m)])
    root = flow("t", "测试", children=[inner])
    run(root, RunConfig(entry_id="t.inner.m", params={"x": "override"}))
    assert got == ["override"]


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
    assert len(root.children) == 8
    reg = FlowRegistry.build(root)
    assert "fee_day.mail.open" in reg.nodes


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
            ("data/ming_jiang_sha/fee_day/mail/email.png",),
            threshold=0.8,
            timeout=30.0,
            interval=0.1,
            region=None,
            grayscale=None,
        )
