"""赠礼优先表选槽 / 选类别。"""

from vision_workflow.apps.ming_jiang_sha.parts.qian_li_dan_qi.utils import (
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
    slot = pick_reward_slot(["吕布赠礼", "马超赠礼", "陆逊赠礼"], state)
    assert slot == 1


def test_pick_skips_obtained_key_rewards() -> None:
    state = BattleState()
    state.mark_reward(RewardKind.TOKEN)
    state.mark_reward(RewardKind.BUFF)
    slot = pick_reward_slot(["马超赠礼", "吕布赠礼", "陆逊赠礼"], state)
    assert slot == 2


def test_pick_fallback_prefers_buff_then_left() -> None:
    state = BattleState()
    state.mark_reward(RewardKind.TOKEN)
    state.mark_reward(RewardKind.BUFF)
    state.mark_reward(RewardKind.CARD)
    slot = pick_reward_slot(["陆逊赠礼", "吕布赠礼", "马超赠礼"], state)
    assert slot == 1


def test_pick_unknown_defaults_leftmost() -> None:
    state = BattleState()
    slot = pick_reward_slot(["张飞赠礼", "关羽赠礼", "刘备赠礼"], state)
    assert slot == 0


def test_resolve_general_priority_known_and_unknown() -> None:
    known = resolve_general_priority("马超")
    assert known.name == "马超"
    assert RewardKind.TOKEN in known.key_rewards
    unknown = resolve_general_priority("张飞")
    assert unknown.name == "张飞"
    assert unknown.key_rewards == ()


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
    state.mark_reward(RewardKind.TOKEN)
    assert (
        pick_reward_kind({RewardKind.BUFF, RewardKind.TOKEN}, entry, state)
        == RewardKind.BUFF
    )
    state.mark_reward(RewardKind.BUFF)
    assert (
        pick_reward_kind({RewardKind.JOINT, RewardKind.CARD}, entry, state)
        == RewardKind.CARD
    )
