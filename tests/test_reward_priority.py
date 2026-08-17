"""赠礼优先表选槽 / 选类别。"""

from vision_workflow.apps.ming_jiang_sha.parts.qian_li_dan_qi.utils import (
    DEFAULT_KEY_REWARDS,
    BattleState,
    GeneralPriority,
    RewardKind,
    parse_general_name,
    pick_reward_kind,
    pick_reward_slot,
    resolve_general_priority,
)


def test_parse_general_name_strips_suffix() -> None:
    assert parse_general_name("马超赠礼") == "马超"
    assert parse_general_name("吕布") == "吕布"
    assert parse_general_name("") == ""
    assert parse_general_name("(空)") == ""


def test_pick_primary_table_order_when_needed() -> None:
    state = BattleState()
    # PRIORITY 中吕布在马超前
    slot = pick_reward_slot(["马超赠礼", "吕布赠礼", "陆逊赠礼"], state)
    assert slot == 1


def test_pick_skips_only_when_all_key_rewards_done() -> None:
    """关键奖励要全部拿完才跳过；只拿过其中一个仍可选。"""
    state = BattleState()
    # 甘宁关键：信物 + 驰援；只记了信物 → 仍应选甘宁（比后面的刘表优先）
    state.mark_general_reward("甘宁", RewardKind.TOKEN)
    slot = pick_reward_slot(["刘表赠礼", "甘宁赠礼", "萧何赠礼"], state)
    assert slot == 1

    # 信物、驰援都拿过 → 跳过甘宁，选刘表
    state.mark_general_reward("甘宁", RewardKind.BUFF)
    slot = pick_reward_slot(["刘表赠礼", "甘宁赠礼", "萧何赠礼"], state)
    assert slot == 0


def test_pick_skips_obtained_key_rewards() -> None:
    state = BattleState()
    state.mark_general_reward("吕布", RewardKind.TOKEN)
    state.mark_general_reward("马超", RewardKind.BUFF)
    # 吕布/马超关键已拿完；鲁肃仍要资助
    slot = pick_reward_slot(["马超赠礼", "吕布赠礼", "鲁肃赠礼"], state)
    assert slot == 2


def test_pick_fallback_among_table_when_all_key_done() -> None:
    state = BattleState()
    for name in ("陆逊", "吕布", "马超"):
        for kind in RewardKind:
            state.mark_general_reward(name, kind)
    slot = pick_reward_slot(["陆逊赠礼", "吕布赠礼", "马超赠礼"], state)
    assert slot == 0


def test_pick_unknown_defaults_leftmost() -> None:
    state = BattleState()
    slot = pick_reward_slot(["张飞赠礼", "赵云赠礼", "刘备赠礼"], state)
    assert slot == 0


def test_resolve_general_priority_known_and_unknown() -> None:
    known = resolve_general_priority("马超")
    assert known.name == "马超"
    assert known.key_rewards == (RewardKind.BUFF,)
    unknown = resolve_general_priority("张飞")
    assert unknown.name == "张飞"
    assert unknown.key_rewards == DEFAULT_KEY_REWARDS


def test_reward_kind_labels() -> None:
    assert RewardKind.HELP == "资助"
    assert RewardKind.BUFF == "驰援"


def test_pick_reward_kind_prefers_pending_key_then_fallback() -> None:
    state = BattleState()
    entry = GeneralPriority("马超", (RewardKind.TOKEN, RewardKind.BUFF))
    assert (
        pick_reward_kind({RewardKind.BUFF, RewardKind.TOKEN}, entry, state)
        == RewardKind.TOKEN
    )
    state.mark_general_reward("马超", RewardKind.TOKEN)
    assert (
        pick_reward_kind({RewardKind.BUFF, RewardKind.TOKEN}, entry, state)
        == RewardKind.BUFF
    )
    state.mark_general_reward("马超", RewardKind.BUFF)
    assert (
        pick_reward_kind({RewardKind.JOINT, RewardKind.CARD}, entry, state)
        == RewardKind.CARD
    )
