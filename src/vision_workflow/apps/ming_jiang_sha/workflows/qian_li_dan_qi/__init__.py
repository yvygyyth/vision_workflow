"""复杂流程：千里单骑。"""

from vision_workflow.apps.ming_jiang_sha.parts.qian_li_dan_qi.ba_qing_store import (
    FLOW as ba_qing_store,
)
from vision_workflow.apps.ming_jiang_sha.parts.qian_li_dan_qi.battle_select import (
    FLOW as battle_select,
)
from vision_workflow.apps.ming_jiang_sha.parts.qian_li_dan_qi.battle_select.actions import (
    EventChoice,
    ShopChoice,
)
from vision_workflow.apps.ming_jiang_sha.parts.qian_li_dan_qi.enter_battle import (
    FLOW as enter_battle,
)
from vision_workflow.apps.ming_jiang_sha.parts.qian_li_dan_qi.fei_fei import (
    FLOW as fei_fei,
)
from vision_workflow.apps.ming_jiang_sha.parts.qian_li_dan_qi.mo_zi import (
    FLOW as mo_zi,
)
from vision_workflow.apps.ming_jiang_sha.parts.qian_li_dan_qi.fight import (
    FLOW as fight,
    FLOW_IN_BATTLE as in_battle,
)
from vision_workflow.apps.ming_jiang_sha.parts.qian_li_dan_qi.pocket_event import (
    FLOW as pocket_event,
)
from vision_workflow.apps.ming_jiang_sha.parts.qian_li_dan_qi.rest import (
    FLOW as rest,
)
from vision_workflow.apps.ming_jiang_sha.parts.qian_li_dan_qi.run_ended import (
    FLOW as run_ended,
    RUN_ENDED,
)
from vision_workflow.apps.ming_jiang_sha.parts.qian_li_dan_qi.shi_chang_shi import (
    FLOW as shi_chang_shi,
)
from vision_workflow.apps.ming_jiang_sha.parts.qian_li_dan_qi.utils import (
    bind_battle_state,
    clear_battle_state,
)
from vision_workflow.apps.ming_jiang_sha.parts.qian_li_dan_qi.zhu_ge_liang import (
    FLOW as zhu_ge_liang,
)
from vision_workflow.module import FlowNode, FlowRouter, Workflow, WorkflowLifecycle
from vision_workflow.status import FlowStatus

_BACK_TO_SELECT = FlowRouter(
    on={
        FlowStatus.FULFILLED: "battle_select",
        FlowStatus.REJECTED: None,
    }
)

_FIGHT_ROUTER = FlowRouter(
    on={
        FlowStatus.FULFILLED: "battle_select",
        RUN_ENDED: "run_ended",
        FlowStatus.REJECTED: None,
    }
)

WORKFLOW = Workflow(
    id="qian_li_dan_qi",
    name="千里单骑",
    description="千里单骑",
    entry="enter_battle",
    lifecycle=WorkflowLifecycle(
        on_enter=bind_battle_state,
        on_exit=clear_battle_state,
    ),
    nodes=[
        FlowNode(enter_battle, params={"wu_jiang": "吕布"}),
        FlowNode(
            battle_select,
            router=FlowRouter(
                on={
                    FlowStatus.FULFILLED: "fight",
                    ShopChoice.BA_QING_STORE: "ba_qing_store",
                    ShopChoice.POCKET_EVENT: "pocket_event",
                    ShopChoice.REST: "rest",
                    EventChoice.ZHU_GE_LIANG: "zhu_ge_liang",
                    EventChoice.FEI_FEI: "fei_fei",
                    EventChoice.SHI_CHANG_SHI: "shi_chang_shi",
                    EventChoice.MO_ZI: "mo_zi",
                    RUN_ENDED: "run_ended",
                    FlowStatus.REJECTED: None,
                }
            ),
        ),
        FlowNode(ba_qing_store, router=_BACK_TO_SELECT),
        FlowNode(rest, router=_BACK_TO_SELECT),
        FlowNode(
            pocket_event,
            router=FlowRouter(
                on={
                    FlowStatus.FULFILLED: "battle_select",
                    "in_battle": "in_battle",
                    FlowStatus.REJECTED: None,
                }
            ),
        ),
        FlowNode(zhu_ge_liang, router=_BACK_TO_SELECT),
        FlowNode(fei_fei, router=_BACK_TO_SELECT),
        FlowNode(mo_zi, router=_BACK_TO_SELECT),
        FlowNode(
            shi_chang_shi,
            router=FlowRouter(
                on={
                    FlowStatus.FULFILLED: "in_battle",
                    FlowStatus.REJECTED: None,
                }
            ),
        ),
        FlowNode(in_battle, router=_FIGHT_ROUTER),
        FlowNode(fight, router=_FIGHT_ROUTER),
        FlowNode(
            run_ended,
            router=FlowRouter(
                on={
                    FlowStatus.FULFILLED: "enter_battle",
                    FlowStatus.REJECTED: None,
                }
            ),
        ),
    ],
)
