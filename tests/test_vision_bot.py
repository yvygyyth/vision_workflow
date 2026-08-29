"""vision_bot 测试。"""

import threading
import time
from pathlib import Path

import pytest

from vision_bot.apps.ming_jiang_sha.paths import QLDQ
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.build import build_qian_li_dan_qi
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.flows.battle_hub import (
    CHALLENGE,
    relocate as relocate_hub,
)
from vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.flows.qian_li import relocate as relocate_qian_li
from vision_bot.core.models import MatchResult
from vision_bot.runtime import flow, mod, run
from vision_bot.runtime.catalog import ROOT_FLOWS, get_root_flow, root_flow_choices
from vision_bot.runtime.config import RunConfig
from vision_bot.runtime.context import RunContext
from vision_bot.runtime.registry import FlowRegistry
from vision_bot.runtime.relocate import RelocateRule, resolve
from vision_bot.runtime.result import Result
from vision_bot.vision import ScreenSnapshot


def test_detect_qian_li_hub(monkeypatch: pytest.MonkeyPatch) -> None:
    battle_interface = f"{QLDQ}/enter_battle/battle_interface.png"

    def fake_snap(*images, region=None, **kwargs):
        flat: list[str] = []
        for item in images:
            if isinstance(item, str):
                flat.append(item)
            else:
                flat.extend(item)
        if len(flat) == 1 and flat[0] == battle_interface:
            return Result.success(
                value=MatchResult(found=True, image=battle_interface)
            )
        return ScreenSnapshot(hits={})

    monkeypatch.setattr(
        "vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.flows.qian_li.snap",
        fake_snap,
    )
    outcome = resolve(relocate_qian_li, RunContext())
    assert outcome is not None and outcome.ok
    assert outcome.then == "qldq.battle_hub"


def test_relocate_hub_pick_battle(monkeypatch: pytest.MonkeyPatch) -> None:
    shot = ScreenSnapshot(
        hits={CHALLENGE: Result.success(value=MatchResult(found=True, image=CHALLENGE))}
    )

    def fake_snap(templates, region=None):
        if isinstance(templates, str):
            return Result.fail("no")
        return shot

    monkeypatch.setattr(
        "vision_bot.apps.ming_jiang_sha.qian_li_dan_qi.flows.battle_hub.snap",
        fake_snap,
    )
    outcome = resolve(relocate_hub, RunContext())
    assert outcome is not None and outcome.ok
    assert outcome.then == "qldq.battle_hub.pick_battle"


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
        return Result.success(then="t.c")

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


def test_call_tool_relocate_parent_uses_caller() -> None:
    """call 的工具 Flow relocate 未命中 → fail 时，走调用方 Flow 的 relocate。"""
    from vision_bot.perception.session import bind_perception
    from vision_bot.runtime.bind import bind_runtime
    from vision_bot.runtime.runner import Runner

    log: list[str] = []

    def tool_step(ctx):
        log.append("tool")
        ctx.vars["need_recover"] = True
        return Result.fail("工具失败")

    def recover(ctx):
        log.append("recover")
        return Result.success()

    def caller(ctx):
        log.append("caller")
        return ctx.call("tool")

    tool = flow(
        "tool",
        "工具",
        children=[mod("tool.m", "T", tool_step)],
        # 配置了但永不命中 → resolve 返回 fail → 上交 call 方
        relocate=[RelocateRule(when=lambda ctx: False, then="tool.m")],
    )
    root = flow(
        "t",
        "根",
        children=[
            mod("t.caller", "C", caller),
            mod("t.recover", "R", recover),
        ],
        # 仅失败后标记才恢复，避免入口就跳到 recover
        relocate=[
            RelocateRule(
                when=lambda ctx: bool(ctx.vars.get("need_recover")),
                then="t.recover",
            ),
            # 入口未标记时不跳转（否则全部未命中 → fail → 根耗尽）
            RelocateRule(when=lambda ctx: True, then=None),
        ],
    )
    reg = FlowRegistry.build(root)
    reg.register_tool(tool)

    bind_perception(Path(".").resolve())
    ctx = RunContext()
    runner = Runner(ctx, reg, root=root)
    ctx._runner = runner
    bind_runtime(ctx)
    result = runner.run_flow(root)
    assert result.ok
    assert log == ["caller", "tool", "recover"]


def test_call_runs_sync_and_resumes() -> None:
    """call 同步跑完目标后回到调用方，可继续执行。"""
    log: list[str] = []

    def a(ctx):
        log.append("a")
        r = ctx.call("t.c")
        assert r.ok
        log.append("a-after")
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
    # call 同步跑 c 后回到 a；a 结束后继续兄弟 b、c
    assert log == ["a", "c", "a-after", "b", "c"]


def test_relocate_on_entry() -> None:
    log: list[str] = []

    def a(ctx):
        log.append("a")
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
        relocate=[RelocateRule(when=lambda ctx: True, then="t.b")],
    )
    report = run(root, RunConfig(), base_dir=Path("."))
    assert report.success
    # relocate 到 b 后继续跑后续兄弟 c
    assert log == ["b", "c"]


def test_relocate_parent_on_entry() -> None:
    """子 Flow relocate fail → 走父级 relocate。"""
    log: list[str] = []

    def leaf(ctx):
        log.append("leaf")
        return Result.success()

    def other(ctx):
        log.append("other")
        return Result.success()

    inner = flow(
        "t.inner",
        "内",
        children=[mod("t.inner.leaf", "叶", leaf)],
        relocate=[RelocateRule(when=lambda ctx: True, then=Result.fail("上交"))],
    )
    root = flow(
        "t",
        "根",
        children=[
            mod("t.other", "另", other),
            inner,
        ],
        relocate=[RelocateRule(when=lambda ctx: True, then="t.other")],
    )
    report = run(root, RunConfig(entry_id="t.inner"), base_dir=Path("."))
    assert report.success
    assert log == ["other"]


def test_relocate_none_keeps_first_child() -> None:
    """命中 then=None：不跳转，按顺序跑第一个 child（不因未配置而 PARENT）。"""
    log: list[str] = []

    def leaf(ctx):
        log.append("leaf")
        return Result.success()

    def other(ctx):
        log.append("other")
        return Result.success()

    inner = flow(
        "t.inner",
        "内",
        children=[mod("t.inner.leaf", "叶", leaf)],
        relocate=[RelocateRule(when=lambda ctx: True, then=None)],
    )
    root = flow(
        "t",
        "根",
        children=[
            mod("t.other", "另", other),
            inner,
        ],
        relocate=[RelocateRule(when=lambda ctx: True, then="t.other")],
    )
    report = run(root, RunConfig(entry_id="t.inner"), base_dir=Path("."))
    assert report.success
    assert log == ["leaf"]


def test_relocate_unmatched_goes_parent() -> None:
    """配置了 relocate 但全部未命中 → fail 上交父级。"""
    log: list[str] = []

    def leaf(ctx):
        log.append("leaf")
        return Result.success()

    def other(ctx):
        log.append("other")
        return Result.success()

    inner = flow(
        "t.inner",
        "内",
        children=[mod("t.inner.leaf", "叶", leaf)],
        relocate=[RelocateRule(when=lambda ctx: False, then="t.inner.leaf")],
    )
    root = flow(
        "t",
        "根",
        children=[
            mod("t.other", "另", other),
            inner,
        ],
        relocate=[RelocateRule(when=lambda ctx: True, then="t.other")],
    )
    report = run(root, RunConfig(entry_id="t.inner"), base_dir=Path("."))
    assert report.success
    assert log == ["other"]


def test_relocate_omitted_runs_first_child() -> None:
    """未传 relocate → 直接 children[0]。"""
    log: list[str] = []

    def a(ctx):
        log.append("a")
        return Result.success()

    root = flow("t", "根", children=[mod("t.a", "A", a)])
    report = run(root, RunConfig(), base_dir=Path("."))
    assert report.success
    assert log == ["a"]


def test_relocate_parent_at_root_stops() -> None:
    """根节点 relocate fail → 直接停止，不跑 children。"""
    log: list[str] = []

    def a(ctx):
        log.append("a")
        return Result.success()

    root = flow(
        "t",
        "根",
        children=[mod("t.a", "A", a)],
        relocate=[RelocateRule(when=lambda ctx: True, then=Result.fail("无父级"))],
    )
    report = run(root, RunConfig(), base_dir=Path("."))
    assert not report.success
    assert log == []


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
