from __future__ import annotations
from pathlib import Path
from . import oiar_069_historical_pre_settlement_coverage_acquisition_gap_physical_trace as b69
from . import oiar_070_active_only_coverage_semantics_physical_proof as b70
from . import oiar_072_historical_recovery_semantics_boundary_proof as b72

BUILD_ID="OIAR-073"
REVISION="OIAR_073_CURRENT_RECOVERY_CONTRACT_DECISION_GATE_REBUILD_V1"

def physical_probe(root=None):
    root=Path(root or Path.cwd()).resolve()
    x=b69.trace(root,50)
    c=b70.contract_probe()
    r=b72.physical_probe(root)

    before=int(x["before_opc_coverage_epoch"])
    inside=int(x["inside_opc_coverage_epoch_without_snapshot"])

    # Current certified OIAR-072 contract:
    # OBR-004 preserves explicit NO_LIVE_EVIDENCE_DURING_GAP lineage,
    # OHL requires genuine pre-settlement evidence, and fabrication is forbidden.
    explicit_missing_lineage=bool(r["obr_004_missing_live_evidence_lineage_explicit"])
    requires_pre=bool(r["ohl_requires_pre_settlement_evidence"])
    rejects_leakage=bool(r["ohl_rejects_post_outcome_leakage"])
    no_fabrication=not bool(r["historical_pre_settlement_fabrication_allowed"])

    if inside>before:
        decision="IN_COVERAGE_ERA_ROTATION_OR_ADMISSION_GAP"
        nxt="OPC_FORWARD_COVERAGE_LATENCY_AND_SETTLEMENT_AWARENESS_PAVEMENT"
    elif before>0:
        decision="LEGACY_PRE_COVERAGE_HISTORY_GAP"
        nxt="FORWARD_COVERAGE_PLUS_EXPLICIT_UNRECOVERABLE_HISTORY_LINEAGE"
    else:
        decision="NO_DOMINANT_UPSTREAM_GAP_CLASSIFIED"
        nxt="RETURN_TO_EXACT_EVIDENCE_LINKAGE_DIAGNOSTIC"

    return {
      "sample_size":int(x["sampled_missing_settlements"]),
      "before_coverage_epoch":before,
      "inside_coverage_epoch_missing_snapshot":inside,
      "pre_settlement_snapshot_found":int(x["pre_settlement_snapshot_found"]),
      "post_only_snapshot_found":int(x["post_only_snapshot_found"]),
      "active_only_normal_coverage":not bool(c["historical_settled_backfill_supported_by_normal_cycle"]),
      "explicit_missing_live_evidence_lineage":explicit_missing_lineage,
      "historical_learning_requires_pre_settlement_evidence":requires_pre,
      "historical_learning_rejects_post_outcome_leakage":rejects_leakage,
      "historical_evidence_fabrication_forbidden":no_fabrication,
      "decision":decision,
      "next_pavement":nxt,
      "read_only":True,
      "repaired_rows":0,
      "probability_enabled":False,
      "execution_authority":False,
    }

def verify_oiar_073():
    return BUILD_ID=="OIAR-073"
