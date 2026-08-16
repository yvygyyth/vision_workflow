"""赠礼优先表选槽。"""

from vision_workflow.apps.ming_jiang_sha.parts.qian_li_dan_qi.utils import (
    BattleState,
    RewardKind,
    parse_general_name,
    pick_reward_slot,
)


def test_parse_general_name_strips_suffix() -> None:
    assert parse_general_name("马超赠礼") == "马超"
    assert parse_general_name("吕布") == "吕布"
    assert parse_general_name("") == ""
    assert parse_general_name("(空)") == ""


def test_pick_primary_table_order_when_needed() -> None:
    state = BattleState()
    # 表顺序马超优先于吕布；二者都缺关键奖励
    slot = pick_reward_slot(["吕布赠礼", "马超赠礼", "陆逊赠礼"], state)
    assert slot == 1


def test_pick_skips_obtained_key_rewards() -> None:
    state = BattleState()
    state.mark_reward(RewardKind.TOKEN)
    state.mark_reward(RewardKind.REINFORCE)
    # 马超/吕布关键奖励已齐；陆逊仍缺武将牌 → 选陆逊
    slot = pick_reward_slot(["马超赠礼", "吕布赠礼", "陆逊赠礼"], state)
    assert slot == 2


def test_pick_fallback_prefers_reinforce_then_left() -> None:
    state = BattleState()
    state.mark_reward(RewardKind.TOKEN)
    state.mark_reward(RewardKind.REINFORCE)
    state.mark_reward(RewardKind.GENERAL_CARD)
    # 全部关键已齐 → 回退：吕布关键含驰援，优于陆逊武将牌
    slot = pick_reward_slot(["陆逊赠礼", "吕布赠礼", "马超赠礼"], state)
    assert slot == 1


def test_pick_unknown_defaults_leftmost() -> None:
    state = BattleState()
    slot = pick_reward_slot(["张飞赠礼", "关羽赠礼", "刘备赠礼"], state)
    assert slot == 0
