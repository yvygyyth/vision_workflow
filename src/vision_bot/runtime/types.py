"""Flow / Module 运行时约定 outcome key。"""

from __future__ import annotations

# 框架
OK = "ok"
FAIL = "fail"
ESCALATE = "escalate"

# 千里业务（跨 Flow 路由）
BACK_TO_HUB = "back_to_hub"
FIGHT = "fight"
ENTER_BATTLE = "enter_battle"
RUN_ENDED = "run_ended"
BA_QING_STORE = "ba_qing_store"
POCKET_EVENT = "pocket_event"
REST = "rest"
FEI_FEI = "fei_fei"
MO_ZI = "mo_zi"
SHI_CHANG_SHI = "shi_chang_shi"

# Module 内部分支
STILL_HERE = "still_here"
SKIP = "skip"

# runner 哨兵：本 Flow 结束，向父级返回 outcome
END = "__end__"

OutcomeKey = str
