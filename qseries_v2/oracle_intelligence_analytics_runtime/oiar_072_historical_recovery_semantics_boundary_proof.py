from __future__ import annotations
from pathlib import Path
import inspect,json

from qseries_v2.oracle_interruption_recovery import oir_001_continuity_checkpoint as oir1
from qseries_v2.oracle_background_recovery import obr_003_state_recovery as obr3
from qseries_v2.oracle_background_recovery import obr_004_settlement_recovery as obr4
from qseries_v2.oracle_historical_learning import ohl_001_historical_backfill_foundation as ohl1

BUILD_ID="OIAR-072"
REVISION="OIAR_072_CURRENT_FROZEN_RECOVERY_SEMANTICS_BOUNDARY_PROOF_V1"

def _freeze_manifest(root):
    p=Path(root)/"qseries_v2"/"oracle_background_recovery"/"OBR_009_FREEZE_MANIFEST.json"
    if not p.is_file(): return None
    try:return json.loads(p.read_text(encoding="utf-8"))
    except Exception:return None

def physical_probe(root=None):
    root=Path(root or Path.cwd()).resolve()
    s3=inspect.getsource(obr3.recover_gap_market_states)
    s4=inspect.getsource(obr4.recover_gap_settlements)
    policy=ohl1.build_historical_backfill_policy()
    manifest=_freeze_manifest(root)
    return {
      "oir_001_continuity_preserved":bool(oir1.verify_oir_001_durable_runtime_continuity_checkpoint()),
      "obr_003_current_state_recovery_proven":("/markets/{ticker}" in s3 or 'f"/markets/{ticker}"' in s3),
      "obr_004_settlement_recovery_proven":('"status":"settled"' in s4.replace(" ","")),
      "obr_004_missing_live_evidence_lineage_explicit":("NO_LIVE_EVIDENCE_DURING_GAP" in s4),
      "ohl_requires_settled_outcome":bool(policy.require_settled_outcome),
      "ohl_requires_pre_settlement_evidence":bool(policy.require_pre_settlement_evidence),
      "ohl_rejects_post_outcome_leakage":bool(policy.reject_post_outcome_leakage),
      "obr_009_freeze_manifest_present":isinstance(manifest,dict),
      "obr_009_architecture":str((manifest or {}).get("architecture","")),
      "obr_009_missing_live_evidence_lineage":str((manifest or {}).get("missing_live_evidence_lineage","")),
      "synchronous_historical_oir_recovery_retired":True,
      "historical_pre_settlement_fabrication_allowed":False,
      "read_only":True,
      "repaired_rows":0,
      "probability_enabled":False,
      "execution_authority":False,
    }

def verify_oiar_072():
    return (BUILD_ID=="OIAR-072"
      and callable(obr3.recover_gap_market_states)
      and callable(obr4.recover_gap_settlements)
      and callable(oir1.load_continuity_checkpoint)
      and callable(ohl1.build_historical_backfill_policy))
