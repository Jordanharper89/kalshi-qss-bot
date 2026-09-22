from pathlib import Path
from qseries_v2.oracle_pre_settlement_coverage.opc_049_post_repair_settlement_cohort_read_model import physical_probe as cohort
from qseries_v2.oracle_pre_settlement_coverage.opc_050_post_repair_presettlement_evidence_gate import physical_probe as evidence
from qseries_v2.oracle_pre_settlement_coverage.opc_051_post_repair_learning_linkage_gate import physical_probe as linkage
OPC_052_BUILD_ID="OPC-052"
def physical_probe(root=None):
 root=Path(root or Path.cwd()).resolve();a=cohort(root);b=evidence(root);c=linkage(root)
 if a["post_repair_settlements"]==0:status="WAITING_FOR_POST_REPAIR_SETTLEMENTS"
 elif b["with_pre_settlement_snapshot"]==0:status="HOLD_NO_POST_REPAIR_PRESETTLEMENT_EVIDENCE"
 elif c["linked"]==0:status="HOLD_LEARNING_LINKAGE_NOT_RECONNECTED"
 elif c["learned"]==0 and c["eligible"]==0:status="HOLD_NO_ELIGIBLE_OR_LEARNED_POST_REPAIR_OUTCOME"
 else:status="POST_REPAIR_OUTCOME_LEARNING_RECONNECTED"
 return {"gate_status":status,"post_repair_settlements":a["post_repair_settlements"],"with_pre_settlement_snapshot":b["with_pre_settlement_snapshot"],"linked":c["linked"],"eligible":c["eligible"],"learned":c["learned"],"calibration_ready":status=="POST_REPAIR_OUTCOME_LEARNING_RECONNECTED","probability_enabled":False,"read_only":True,"execution_authority":False}
def verify_opc_052():return OPC_052_BUILD_ID=="OPC-052"
